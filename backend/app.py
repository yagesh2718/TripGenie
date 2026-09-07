from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.schemas.models import UserTripInput
from backend.graph.workflow import get_compiled_graph
from backend.utils.pdf_generator import create_itinerary_pdf, upload_to_s3
import uuid
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TripGenie API")

class PlanRequest(BaseModel):
    user_input: UserTripInput

@app.post("/api/plan")
async def create_plan(request: PlanRequest):
    thread_id = str(uuid.uuid4())
    graph, conn = await get_compiled_graph()
    
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # We invoke the graph with the initial state
        initial_state = {
            "thread_id": thread_id,
            "user_input": request.user_input,
        }
        
        # Run graph
        result = await graph.ainvoke(initial_state, config=config)
        return {
            "thread_id": thread_id,
            "draft_itinerary": result.get("draft_itinerary"),
            "is_valid": result.get("is_valid"),
            "critic_feedback": result.get("critic_feedback"),
            "retry_count": result.get("retry_count")
        }
    except Exception as e:
        logger.error(f"Error executing graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await conn.close()

@app.get("/api/plan/{thread_id}")
async def get_plan(thread_id: str):
    graph, conn = await get_compiled_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        state = await graph.aget_state(config)
        if not state or not state.values:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        result = state.values
        return {
            "thread_id": thread_id,
            "draft_itinerary": result.get("draft_itinerary"),
            "is_valid": result.get("is_valid"),
            "critic_feedback": result.get("critic_feedback"),
            "retry_count": result.get("retry_count")
        }
    except Exception as e:
        logger.error(f"Error fetching state: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await conn.close()

@app.post("/api/plan/{thread_id}/export-pdf")
async def export_plan_pdf(thread_id: str):
    graph, conn = await get_compiled_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        state = await graph.aget_state(config)
        if not state or not state.values or "draft_itinerary" not in state.values:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        itinerary = state.values["draft_itinerary"]
        if hasattr(itinerary, "model_dump"):
            itinerary = itinerary.model_dump()
            
        pdf_path = create_itinerary_pdf(itinerary)
        url = upload_to_s3(pdf_path)
        
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            
        if not url:
            raise HTTPException(status_code=500, detail="Failed to upload PDF to S3")
            
        return {"url": url}
    except Exception as e:
        logger.error(f"Error exporting PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await conn.close()
