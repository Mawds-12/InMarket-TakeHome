# clients/courtlistener.py
#
# HTTP client for the CourtListener search API.
# All requests use token-based auth read from settings.
#
# Raises: CourtListenerError on non-200 responses or network timeouts.

import httpx
from config import settings
from exceptions import CourtListenerError

_BASE_URL = "https://www.courtlistener.com/api/rest/v4"


async def search_opinions(query: str, state: str, mode: str = "semantic") -> dict:
    """
    Search for case law opinions via CourtListener API.
    
    Args:
        query: Search query string (legal keywords)
        state: State code (e.g., "CA", "NY") or "federal" or "nationwide"
        mode: "semantic" or "keyword" search mode
        
    Returns:
        dict with keys: results (list of case dicts), count (total found)
        
    Raises:
        CourtListenerError: If the API call fails or times out
    """
    headers = {"Authorization": f"Token {settings.courtlistener_api_key}"}
    
    params = {
        "q": query,
        "type": "o",  # opinions
    }
    
    if state not in ("federal", "nationwide"):
        params["court"] = state.lower()
    
    if mode == "semantic":
        params["semantic"] = "true"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_BASE_URL}/search/",
                headers=headers,
                params=params,
                timeout=15.0,
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        raise CourtListenerError("CourtListener request timed out after 15s")
    except httpx.HTTPStatusError as e:
        raise CourtListenerError(f"CourtListener returned {e.response.status_code}")
    except Exception as e:
        raise CourtListenerError(f"CourtListener request failed: {str(e)}")
    
    return response.json()
