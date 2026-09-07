from typing import TypedDict, List, Optional
from backend.schemas.models import (
    UserTripInput,
    FlightOption,
    HotelOption,
    AttractionItem,
    WeatherForecast,
    FinalItinerary
)

class TripState(TypedDict):
    thread_id: str
    user_input: UserTripInput
    
    # Extracted data (parsed strictly to Pydantic objects)
    weather_data: List[WeatherForecast]
    attractions_data: List[AttractionItem]
    flights_data: List[FlightOption]
    hotels_data: List[HotelOption]
    
    # Flow state
    retry_count: int
    draft_itinerary: Optional[FinalItinerary]
    critic_feedback: Optional[str]
    is_valid: bool
