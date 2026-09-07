from backend.schemas.state import TripState

async def router_node(state: TripState) -> dict:
    # Extracts preferences and ensures graph state is initialized
    # Returns the initial dictionary to update the graph state
    return {
        "retry_count": 0,
        "is_valid": False,
        "critic_feedback": "",
        "weather_data": [],
        "attractions_data": [],
        "flights_data": [],
        "hotels_data": []
    }
