import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.tools.cache_utils import with_cache
from typing import List, Dict, Any

@with_cache(ttl_seconds=3600 * 24)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_attractions_raw(destination: str) -> List[Dict[str, Any]]:
    # We use nominatim to search for tourism/attractions
    url = "https://nominatim.openstreetmap.org/search.php"
    params = {
        "q": f"tourist attractions in {destination}",
        "format": "jsonv2",
        "limit": 15
    }
    headers = {"User-Agent": "AI-Travel-Planner/1.0"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
