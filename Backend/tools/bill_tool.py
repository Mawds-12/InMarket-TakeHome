# tools/bill_tool.py
#
# Fetches legislative bill candidates from the MCP service.
# Called during Stage B of the orchestration chain.

import json
from models.internal import IssueBundle, RawBill
from services.mcp_client import get_mcp_client
from exceptions import MCPError


async def fetch_bills(issue_bundle: IssueBundle, state: str) -> list[RawBill]:
    """
    Fetch bill results from MCP service.
    
    Args:
        issue_bundle: Issue extraction output with bill_query
        state: Two-letter state code (e.g., "CA", "OR")
        
    Returns:
        List of raw bill results
        
    Raises:
        MCPError: If MCP tool call fails
    """
    try:
        client = get_mcp_client()
        
        result = await client.call_tool(
            "search_bills",
            arguments={
                "query": issue_bundle.bill_query,
                "state": state
            }
        )
        
        if not result.content:
            return []
        
        bills_data = json.loads(result.content[0].text)
        
        return [RawBill(**bill) for bill in bills_data]
        
    except Exception as e:
        raise MCPError(f"Failed to fetch bills from MCP: {str(e)}") from e
