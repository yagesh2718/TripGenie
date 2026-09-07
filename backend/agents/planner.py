from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from backend.config import config
from backend.schemas.models import FinalItinerary
from backend.schemas.state import TripState
import logging
from tenacity import retry, wait_exponential, stop_after_attempt

logger = logging.getLogger(__name__)

def get_mistral_llm():
    return ChatMistralAI(temperature=0.2, model="open-mistral-nemo", api_key=config.MISTRAL_API_KEY)

@retry(wait=wait_exponential(multiplier=2, min=4, max=20), stop=stop_after_attempt(5))
async def invoke_planner_chain(chain, state):
    return await chain.ainvoke({
        "user_input": state["user_input"].model_dump_json(),
        "weather": [w.model_dump_json() for w in state.get("weather_data", [])],
        "attractions": [a.model_dump_json() for a in state.get("attractions_data", [])],
        "flights": [f.model_dump_json() for f in state.get("flights_data", [])] if state.get("flights_data") else [],
        "hotels": [h.model_dump_json() for h in state.get("hotels_data", [])] if state.get("hotels_data") else [],
        "critic_feedback": state.get("critic_feedback", "None")
    })

async def planner_node(state: TripState) -> dict:
    llm = get_mistral_llm()
    structured_llm = llm.with_structured_output(FinalItinerary)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert travel planner. Create a realistic, detailed itinerary based on the user's constraints and the provided data. "
                   "Ensure you include flights and hotels if they were requested and provided. "
                   "Note: The flight prices provided are the TOTAL cost for all travelers. The hotel prices provided are the PER NIGHT cost for a room accommodating all travelers. "
                   "Ensure your total estimated cost correctly accounts for this and the number of days of the trip. "
                   "If the user has a critic_feedback, adjust the itinerary to meet the budget or feasibility requirements."),
        ("user", "User Input: {user_input}\n"
                 "Weather: {weather}\n"
                 "Attractions: {attractions}\n"
                 "Flights: {flights}\n"
                 "Hotels: {hotels}\n"
                 "Critic Feedback: {critic_feedback}")
    ])
    
    chain = prompt | structured_llm
    
    try:
        itinerary = await invoke_planner_chain(chain, state)
        return {"draft_itinerary": itinerary}
    except Exception as e:
        logger.error(f"Planner error: {e}")
        return {"draft_itinerary": None}
