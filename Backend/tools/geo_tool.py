# tools/geo_tool.py
#
# Fetches default state from IP address via the MCP service.

import json
from services.mcp_client import get_mcp_client
from exceptions import MCPError


async def infer_state_from_ip(ip: str) -> str:
    """
    Infer default US state from IP address.
    
    Args:
        ip: IP address to lookup
        
    Returns:
        Two-letter state code (e.g., "CA") or "CA" as fallback
        
    Raises:
        MCPError: If MCP tool call fails
    """
    try:
        client = get_mcp_client()
        
        result = await client.call_tool(
            "get_default_state_from_ip",
            arguments={"ip": ip}
        )
        
        if not result.content:
            return "CA"
        
        geo_data = json.loads(result.content[0].text)
        
        return geo_data.get("state_code") or "CA"
        
    except Exception as e:
        raise MCPError(f"Failed to infer state from IP: {str(e)}") from e
