# tools/case_tool.py
#
# Fetches case law candidates from the MCP service.
# Called during Stage B of the orchestration chain.

import json
from models.internal import IssueBundle, RawCase
from services.mcp_client import get_mcp_client
from exceptions import MCPError


async def fetch_cases(issue_bundle: IssueBundle, state: str, mode: str = "semantic") -> tuple[list[RawCase], dict]:
    """
    Fetch case law results from MCP service.
    
    Args:
        issue_bundle: Issue extraction output with case_query
        state: State code (e.g., "CA", "NY") or "federal" or "nationwide"
        mode: Search mode - "semantic" or "keyword"
        
    Returns:
        Tuple of (list of raw case results, timing metadata dict)
        
    Raises:
        MCPError: If MCP tool call fails
    """
    import time
    try:
        client = get_mcp_client()
        
        start_time = time.time()
        result = await client.call_tool(
            "search_cases",
            arguments={
                "query": issue_bundle.case_query,
                "state": state,
                "mode": mode
            }
        )
        duration_ms = int((time.time() - start_time) * 1000)
        
        if not result.content:
            return [], {"duration_ms": duration_ms, "count": 0}
        
        cases_data = json.loads(result.content[0].text)
        cases = [RawCase(**case) for case in cases_data]
        
        metadata = {
            "duration_ms": duration_ms,
            "count": len(cases)
        }
        
        return cases, metadata
        
    except Exception as e:
        raise MCPError(f"Failed to fetch cases from MCP: {str(e)}") from e
