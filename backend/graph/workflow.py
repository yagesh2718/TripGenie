from langgraph.graph import StateGraph, END, START
from backend.schemas.state import TripState
from backend.agents.router import router_node
from backend.agents.planner import planner_node
from backend.agents.critic import critic_node
from backend.agents.parser import parse_weather, parse_attractions, parse_flights, parse_hotels
from backend.tools.weather import fetch_weather_raw
from backend.tools.attractions import fetch_attractions_raw
from backend.tools.travel_inventory import fetch_flights_raw, fetch_hotels_raw
from backend.graph.edges import should_continue
import asyncio
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import aiosqlite
from backend.config import config
import logging

logger = logging.getLogger(__name__)

async def fetchers_node(state: TripState) -> dict:
    origin = getattr(state["user_input"], "origin", "")
    dest = state["user_input"].destination
    start = state["user_input"].start_date
    end = state["user_input"].end_date
    travelers = state["user_input"].travelers
    
    # Run tools concurrently
    tasks = [
        fetch_weather_raw(dest, start, end),
        fetch_attractions_raw(dest)
    ]
    
    if state["user_input"].needs_flights:
        tasks.append(fetch_flights_raw(origin, dest, start, end, travelers))
    else:
        async def dummy(): return None
        tasks.append(dummy())
        
    if state["user_input"].needs_hotel:
        tasks.append(fetch_hotels_raw(dest, start, end, travelers))
    else:
        async def dummy(): return None
        tasks.append(dummy())

    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Extract raw results safely
    raw_weather = results[0] if not isinstance(results[0], Exception) else {}
    raw_attractions = results[1] if not isinstance(results[1], Exception) else []
    raw_flights = results[2] if not isinstance(results[2], Exception) else {}
    raw_hotels = results[3] if not isinstance(results[3], Exception) else {}
    
    if isinstance(results[0], Exception): logger.error(f"Weather error: {results[0]}")
    if isinstance(results[1], Exception): logger.error(f"Attractions error: {results[1]}")
    
    # Parse concurrently
    parse_tasks = [
        parse_weather(raw_weather),
        parse_attractions(raw_attractions)
    ]
    if raw_flights:
        parse_tasks.append(parse_flights(raw_flights))
    else:
        async def dummy_list(): return []
        parse_tasks.append(dummy_list())
        
    if raw_hotels:
        parse_tasks.append(parse_hotels(raw_hotels))
    else:
        async def dummy_list(): return []
        parse_tasks.append(dummy_list())
        
    parsed_results = await asyncio.gather(*parse_tasks, return_exceptions=True)
    
    return {
        "weather_data": parsed_results[0] if not isinstance(parsed_results[0], Exception) else [],
        "attractions_data": parsed_results[1] if not isinstance(parsed_results[1], Exception) else [],
        "flights_data": parsed_results[2] if not isinstance(parsed_results[2], Exception) else [],
        "hotels_data": parsed_results[3] if not isinstance(parsed_results[3], Exception) else []
    }

def create_graph():
    builder = StateGraph(TripState)
    
    builder.add_node("router", router_node)
    builder.add_node("fetchers", fetchers_node)
    builder.add_node("planner", planner_node)
    builder.add_node("critic", critic_node)
    
    builder.add_edge(START, "router")
    builder.add_edge("router", "fetchers")
    builder.add_edge("fetchers", "planner")
    builder.add_edge("planner", "critic")
    
    builder.add_conditional_edges("critic", should_continue, {"end": END, "planner": "planner"})
    
    return builder

async def get_compiled_graph():
    conn = await aiosqlite.connect(config.DB_PATH)
    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()
    
    graph = create_graph().compile(checkpointer=checkpointer)
    return graph, conn
