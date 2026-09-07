import asyncio
import httpx
from backend.tools.cache_utils import with_cache
from typing import Dict, Any
from backend.config import config
import logging

logger = logging.getLogger(__name__)

@with_cache(ttl_seconds=3600)
async def fetch_flights_raw(origin: str, destination: str, start_date: str, end_date: str, travelers: int) -> Dict[str, Any]:
    if not config.SERPAPI_API_KEY:
        logger.warning("No SERPAPI_API_KEY found, returning empty flights.")
        return {"data": []}
        
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": start_date,
        "return_date": end_date,
        "adults": travelers,
        "currency": "USD",
        "hl": "en",
        "api_key": config.SERPAPI_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            best_flights = data.get("best_flights", [])[:3]
            simplified = []
            for flight in best_flights:
                legs = flight.get("flights", [])
                if not legs:
                    continue
                first_leg = legs[0]
                last_leg = legs[-1]
                simplified.append({
                    "airline": first_leg.get("airline", "Unknown"),
                    "flight_number": first_leg.get("flight_number", "Unknown"),
                    "departure_time": first_leg.get("departure_airport", {}).get("time", ""),
                    "arrival_time": last_leg.get("arrival_airport", {}).get("time", ""),
                    "price": flight.get("price", 0.0)
                })
            return {"data": simplified}
        except Exception as e:
            logger.error(f"Error fetching flights from SerpApi: {e}")
            return {"data": []}

@with_cache(ttl_seconds=3600)
async def fetch_hotels_raw(destination: str, start_date: str, end_date: str, travelers: int) -> Dict[str, Any]:
    if not config.SERPAPI_API_KEY:
        logger.warning("No SERPAPI_API_KEY found, returning empty hotels.")
        return {"data": []}
        
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_hotels",
        "q": destination,
        "check_in_date": start_date,
        "check_out_date": end_date,
        "adults": travelers,
        "currency": "USD",
        "hl": "en",
        "api_key": config.SERPAPI_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            properties = data.get("properties", [])[:3]
            simplified = []
            for prop in properties:
                price_str = prop.get("rate_per_night", {}).get("lowest", "0").replace("$", "").replace(",", "")
                price = float(price_str) if price_str.isdigit() else 0.0
                simplified.append({
                    "name": prop.get("name", "Unknown Hotel"),
                    "address": prop.get("link", destination), 
                    "rating": prop.get("overall_rating", 0.0),
                    "price_per_night": price
                })
            return {"data": simplified}
        except Exception as e:
            logger.error(f"Error fetching hotels from SerpApi: {e}")
            return {"data": []}
