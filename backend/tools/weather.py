import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.tools.cache_utils import with_cache
from typing import Dict, Any

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def get_coordinates(destination: str) -> tuple[float, float]:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": destination, "count": 1, "format": "json"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            return data["results"][0]["latitude"], data["results"][0]["longitude"]
        raise ValueError(f"Could not find coordinates for {destination}")

@with_cache(ttl_seconds=3600)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_weather_raw(destination: str, start_date: str, end_date: str) -> Dict[str, Any]:
    lat, lon = await get_coordinates(destination)
    url = "https://api.open-meteo.com/v1/forecast"
    # open-meteo daily requires timezone, using auto
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
        "timezone": "auto"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()
