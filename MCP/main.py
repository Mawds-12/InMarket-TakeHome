# main.py
#
# FastMCP application entry point for the Legal Research MCP service.
# Exposes tools for IP geolocation, case law search, and legislative search.

from fastmcp import FastMCP
from typing import Literal
from config import settings
from clients import ipinfo, courtlistener, openstates
from normalizers import geo_normalizer, case_normalizer, bill_normalizer
from exceptions import IPInfoError, CourtListenerError, OpenStatesError

mcp = FastMCP(name="LegalResearchMCP")


@mcp.tool
async def get_default_state_from_ip(ip: str) -> dict:
    """
    Infer default US state from IP address using IPinfo API.
    
    This provides a convenience default for jurisdiction selection.
    The result should always be user-editable as VPNs, proxies, and 
    corporate networks frequently misreport location.
    
    Args:
        ip: IP address to lookup (e.g., "8.8.8.8")
        
    Returns:
        Dictionary with country, state, state_code, and confidence level
    """
    try:
        raw = await ipinfo.get_location(ip)
        normalized = geo_normalizer.normalize(raw)
        return normalized
    except IPInfoError:
        return {
            "country": "US",
            "state": None,
            "state_code": None,
            "confidence": "error"
        }
    except Exception:
        return {
            "country": "US",
            "state": None,
            "state_code": None,
            "confidence": "error"
        }


@mcp.tool
async def search_cases(
    query: str,
    state: str,
    mode: Literal["semantic", "keyword"] = "semantic"
) -> list[dict]:
    """
    Search case law using CourtListener API.
    
    Returns relevant legal opinions based on the query and jurisdiction.
    Results are sorted by relevance score and limited to avoid token bloat.
    
    Args:
        query: Legal search query (e.g., "contract formation text message")
        state: State code (e.g., "CA", "NY") or "federal" or "nationwide"
        mode: Search mode - "semantic" for meaning-based, "keyword" for exact terms
        
    Returns:
        List of case result dictionaries with normalized schema
    """
    try:
        raw = await courtlistener.search_opinions(query, state, mode)
        results = raw.get("results", [])
        normalized = case_normalizer.normalize(results)
        return normalized
    except CourtListenerError:
        return []
    except Exception:
        return []


@mcp.tool
async def search_bills(query: str, state: str) -> list[dict]:
    """
    Search state legislation using Open States API.
    
    Returns relevant bills and legislative activity for the given query
    and jurisdiction. Useful for understanding statutory context.
    
    Args:
        query: Legislative search query (e.g., "electronic signatures")
        state: Two-letter state code (e.g., "CA", "OR")
        
    Returns:
        List of bill result dictionaries with normalized schema
    """
    try:
        raw = await openstates.search_bills(query, state)
        results = raw.get("results", [])
        normalized = bill_normalizer.normalize(results)
        return normalized
    except OpenStatesError:
        return []
    except Exception:
        return []


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=settings.mcp_port
    )
