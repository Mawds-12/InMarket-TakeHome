# services/mcp_client.py
#
# Singleton FastMCP client connection to the MCP service.
# Connection established at startup and reused across all requests.

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from config import settings
from exceptions import MCPError

_client: Client | None = None


async def initialize_mcp_client() -> None:
    """
    Initialize the MCP client connection at application startup.
    Must be called once before any requests are handled.
    """
    global _client
    
    try:
        transport = StreamableHttpTransport(url=f"{settings.mcp_base_url}/mcp")
        _client = Client(transport)
        
        # Verify connection by listing tools
        await _client.__aenter__()
        tools = await _client.list_tools()
        
        # tools is a list of tool objects, not an object with .tools attribute
        tool_names = [tool.name for tool in tools]
        required_tools = {"get_default_state_from_ip", "search_cases", "search_bills"}
        
        if not required_tools.issubset(set(tool_names)):
            missing = required_tools - set(tool_names)
            raise MCPError(f"MCP server missing required tools: {missing}")
            
    except Exception as e:
        raise MCPError(f"Failed to initialize MCP client: {str(e)}") from e


def get_mcp_client() -> Client:
    """
    Get the singleton MCP client instance.
    
    Returns:
        Connected MCP client
        
    Raises:
        MCPError: If client not initialized
    """
    if _client is None:
        raise MCPError("MCP client not initialized. Call initialize_mcp_client() at startup.")
    
    return _client


async def close_mcp_client() -> None:
    """
    Close the MCP client connection at application shutdown.
    """
    global _client
    
    if _client is not None:
        await _client.__aexit__(None, None, None)
        _client = None
