# tools/bill_tool.py
#
# Fetches legislative bill candidates from the MCP service.
# Called during Stage B of the orchestration chain.

import json
from models.internal import IssueBundle, RawBill
from services.mcp_client import get_mcp_client
from exceptions import MCPError


async def fetch_bills(issue_bundle: IssueBundle, state: str) -> tuple[list[RawBill], dict]:
    """
    Fetch bill results from MCP service.
    
    Args:
        issue_bundle: Issue extraction output with bill_query
        state: Two-letter state code (e.g., "CA", "OR")
        
    Returns:
        Tuple of (list of raw bill results, timing metadata dict)
        
    Raises:
        MCPError: If MCP tool call fails
    """
    import time
    try:
        client = get_mcp_client()
        
        start_time = time.time()
        result = await client.call_tool(
            "search_bills",
            arguments={
                "query": issue_bundle.bill_query,
                "state": state
            }
        )
        duration_ms = int((time.time() - start_time) * 1000)
        
        if not result.content:
            return [], {"duration_ms": duration_ms, "count": 0}
        
        bills_data = json.loads(result.content[0].text)
        bills = [RawBill(**bill) for bill in bills_data]
        
        metadata = {
            "duration_ms": duration_ms,
            "count": len(bills)
        }
        
        return bills, metadata
        
    except Exception as e:
        raise MCPError(f"Failed to fetch bills from MCP: {str(e)}") from e
