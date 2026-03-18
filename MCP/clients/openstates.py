# clients/openstates.py
#
# HTTP client for the Open States API v3.
# All requests use API key auth read from settings.
#
# Raises: OpenStatesError on non-200 responses or network timeouts.

import httpx
from config import settings
from exceptions import OpenStatesError

_BASE_URL = "https://v3.openstates.org"


async def search_bills(query: str, state: str) -> dict:
    """
    Search for state legislation via Open States API.
    
    Args:
        query: Search query string (legislative keywords)
        state: Two-letter state code (e.g., "CA", "OR")
        
    Returns:
        dict with keys: results (list of bill dicts), pagination info
        
    Raises:
        OpenStatesError: If the API call fails or times out
    """
    headers = {"X-API-Key": settings.open_states_api_key}
    
    params = {
        "q": query,
        "jurisdiction": state.upper(),
        "sort": "relevance",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_BASE_URL}/bills",
                headers=headers,
                params=params,
                timeout=15.0,
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        raise OpenStatesError("Open States request timed out after 15s")
    except httpx.HTTPStatusError as e:
        raise OpenStatesError(f"Open States returned {e.response.status_code}")
    except Exception as e:
        raise OpenStatesError(f"Open States request failed: {str(e)}")
    
    return response.json()
