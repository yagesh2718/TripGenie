from pydantic import BaseModel, Field
from typing import List, Optional

class UserTripInput(BaseModel):
    origin: str = ""
    destination: str
    start_date: str
    end_date: str
    budget: float
    travelers: int = 1
    needs_flights: bool = False
    needs_hotel: bool = False

class FlightOption(BaseModel):
    airline: str
    flight_number: str
    departure_time: str
    arrival_time: str
    estimated_price: float

class HotelOption(BaseModel):
    name: str
    address: str
    rating: Optional[float] = None
    price_per_night: float

class AttractionItem(BaseModel):
    name: str
    type: str # e.g., museum, park, landmark
    estimated_price: float = 0.0
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rating: Optional[float] = None

class WeatherForecast(BaseModel):
    date: str
    temperature_max: float
    temperature_min: float
    precipitation_probability: float
    weather_code: int

class DailyPlan(BaseModel):
    date: str
    morning_activity: str
    afternoon_activity: str
    evening_activity: str
    daily_cost_estimate: float

class FinalItinerary(BaseModel):
    destination: str
    total_budget: float
    estimated_cost: float
    flights: Optional[List[FlightOption]] = None
    hotels: Optional[List[HotelOption]] = None
    daily_plans: List[DailyPlan]
    warning_note: Optional[str] = None
