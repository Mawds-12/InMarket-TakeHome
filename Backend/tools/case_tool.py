# tools/case_tool.py
#
# Fetches case law candidates from the MCP service.
# Called during Stage B of the orchestration chain.

import json
from models.internal import IssueBundle, RawCase
from services.mcp_client import get_mcp_client
from exceptions import MCPError


async def fetch_cases(issue_bundle: IssueBundle, state: str, mode: str = "semantic") -> list[RawCase]:
    """
    Fetch case law results from MCP service.
    
    Args:
        issue_bundle: Issue extraction output with case_query
        state: State code (e.g., "CA", "NY") or "federal" or "nationwide"
        mode: Search mode - "semantic" or "keyword"
        
    Returns:
        List of raw case results
        
    Raises:
        MCPError: If MCP tool call fails
    """
    try:
        client = get_mcp_client()
        
        result = await client.call_tool(
            "search_cases",
            arguments={
                "query": issue_bundle.case_query,
                "state": state,
                "mode": mode
            }
        )
        
        if not result.content:
            return []
        
        cases_data = json.loads(result.content[0].text)
        
        return [RawCase(**case) for case in cases_data]
        
    except Exception as e:
        raise MCPError(f"Failed to fetch cases from MCP: {str(e)}") from e
