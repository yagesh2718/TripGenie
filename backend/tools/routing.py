import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.tools.cache_utils import with_cache
from typing import Dict, Any

@with_cache(ttl_seconds=3600 * 24)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def get_travel_duration_raw(lat1: float, lon1: float, lat2: float, lon2: float) -> Dict[str, Any]:
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
    params = {"overview": "false"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()
