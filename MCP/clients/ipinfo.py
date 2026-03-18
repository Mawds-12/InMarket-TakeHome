# clients/ipinfo.py
#
# HTTP client for the IPinfo geolocation API.
# All requests use token-based auth read from settings.
#
# Raises: IPInfoError on non-200 responses or network timeouts.

import httpx
from config import settings
from exceptions import IPInfoError

_BASE_URL = "https://ipinfo.io"


async def get_location(ip: str) -> dict:
    """
    Get geolocation information for an IP address.
    
    Args:
        ip: IP address to lookup (e.g., "8.8.8.8")
        
    Returns:
        dict with keys: ip, city, region, country, loc, postal, timezone
        
    Raises:
        IPInfoError: If the API call fails or times out
    """
    url = f"{_BASE_URL}/{ip}/json"
    params = {"token": settings.ipinfo_token}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        raise IPInfoError("IPinfo request timed out after 10s")
    except httpx.HTTPStatusError as e:
        raise IPInfoError(f"IPinfo returned {e.response.status_code}")
    except Exception as e:
        raise IPInfoError(f"IPinfo request failed: {str(e)}")
    
    return response.json()
