from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from backend.config import config
from backend.schemas.state import TripState
import logging
from tenacity import retry, wait_exponential, stop_after_attempt
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class CriticEvaluation(BaseModel):
    is_valid: bool = Field(description="True if the itinerary is realistic and within budget, False otherwise")
    feedback: str = Field(description="Specific feedback on what needs to be changed if is_valid is False")

def get_mistral_llm():
    return ChatMistralAI(temperature=0, model="open-mistral-nemo", api_key=config.MISTRAL_API_KEY)

@retry(wait=wait_exponential(multiplier=2, min=4, max=20), stop=stop_after_attempt(5))
async def invoke_critic_chain(chain, budget, draft):
    return await chain.ainvoke({
        "budget": budget,
        "draft": draft
    })

async def critic_node(state: TripState) -> dict:
    draft = state.get("draft_itinerary")
    if not draft:
        return {"is_valid": False, "critic_feedback": "Draft itinerary is missing."}
        
    llm = get_mistral_llm()
    structured_llm = llm.with_structured_output(CriticEvaluation)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert travel critic. Evaluate the provided itinerary for feasibility and budget constraints. "
                   "If it exceeds the budget or is completely unrealistic, set is_valid to False and provide actionable feedback. "
                   "Otherwise, set is_valid to True and feedback to 'Looks good!'"),
        ("user", "Budget: {budget}\nDraft Itinerary: {draft}")
    ])
    
    chain = prompt | structured_llm
    
    try:
        evaluation = await invoke_critic_chain(chain, state["user_input"].budget, draft.model_dump_json())
        return {
            "is_valid": evaluation.is_valid,
            "critic_feedback": evaluation.feedback,
            "retry_count": state.get("retry_count", 0) + 1
        }
    except Exception as e:
        logger.error(f"Critic error: {e}")
        return {"is_valid": False, "critic_feedback": "Critic failed to evaluate.", "retry_count": state.get("retry_count", 0) + 1}
