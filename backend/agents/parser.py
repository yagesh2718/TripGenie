import json
from backend.config import config
from backend.schemas.models import WeatherForecast, AttractionItem, FlightOption, HotelOption
from typing import List, Dict, Any
from pydantic import BaseModel
import logging
from tenacity import retry, wait_exponential, stop_after_attempt
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

class WeatherList(BaseModel):
    items: List[WeatherForecast]

class AttractionList(BaseModel):
    items: List[AttractionItem]

class FlightList(BaseModel):
    items: List[FlightOption]

class HotelList(BaseModel):
    items: List[HotelOption]

def get_parser_llm():
    return ChatGroq(temperature=0, model_name="openai/gpt-oss-20b", api_key=config.GROQ_API_KEY)

@retry(wait=wait_exponential(multiplier=2, min=4, max=20), stop=stop_after_attempt(5))
async def invoke_parser(structured_llm, prompt):
    return await structured_llm.ainvoke(prompt)

async def parse_weather(raw_data: Dict[str, Any]) -> List[WeatherForecast]:
    if not raw_data: return []
    llm = get_parser_llm()
    structured_llm = llm.with_structured_output(WeatherList)
    prompt = f"Extract weather forecasts from the following raw JSON:\n{json.dumps(raw_data)[:15000]}"
    try:
        res = await invoke_parser(structured_llm, prompt)
        return res.items
    except Exception as e:
        logger.error(f"Error parsing weather with parser LLM: {e}")
        return []

async def parse_attractions(raw_data: List[Dict[str, Any]]) -> List[AttractionItem]:
    if not raw_data: return []
    llm = get_parser_llm()
    structured_llm = llm.with_structured_output(AttractionList)
    prompt = f"Extract tourist attractions from the following raw JSON:\n{json.dumps(raw_data)[:15000]}"
    try:
        res = await invoke_parser(structured_llm, prompt)
        return res.items
    except Exception as e:
        logger.error(f"Error parsing attractions with parser LLM: {e}")
        return []

async def parse_flights(raw_data: Dict[str, Any]) -> List[FlightOption]:
    if not raw_data: return []
    llm = get_parser_llm()
    structured_llm = llm.with_structured_output(FlightList)
    prompt = f"Extract flight options from the following raw JSON:\n{json.dumps(raw_data)[:15000]}"
    try:
        res = await invoke_parser(structured_llm, prompt)
        return res.items
    except Exception as e:
        logger.error(f"Error parsing flights with parser LLM: {e}")
        return []

async def parse_hotels(raw_data: Dict[str, Any]) -> List[HotelOption]:
    if not raw_data: return []
    llm = get_parser_llm()
    structured_llm = llm.with_structured_output(HotelList)
    prompt = f"Extract hotel options from the following raw JSON:\n{json.dumps(raw_data)[:15000]}"
    try:
        res = await invoke_parser(structured_llm, prompt)
        return res.items
    except Exception as e:
        logger.error(f"Error parsing hotels with parser LLM: {e}")
        return []
