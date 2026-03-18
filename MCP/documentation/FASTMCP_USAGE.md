# FastMCP Usage Guide - Legal Research MCP Service

This document describes how to use the Legal Research MCP service built with the FastMCP framework.

## Architecture

The MCP service has been converted from FastAPI to **FastMCP framework**, which implements the Model Context Protocol. It exposes three tools over Streamable HTTP transport:

1. `get_default_state_from_ip` - IP-based geolocation
2. `search_cases` - CourtListener case law search
3. `search_bills` - Open States legislative search

## Starting the Server

### Development Mode

From the project root:
```bash
npm run dev:mcp
```

Or directly:
```bash
cd MCP
python main.py
```

The server will start on `http://localhost:8001/mcp` using Streamable HTTP transport.

### Production Mode

```bash
cd MCP
python main.py
```

Configure the port via `.env`:
```
MCP_PORT=8001
```

## Available Tools

### 1. get_default_state_from_ip

Infer default US state from IP address using IPinfo API.

**Parameters:**
- `ip` (str): IP address to lookup (e.g., "8.8.8.8")

**Returns:**
```json
{
  "country": "US",
  "state": "California",
  "state_code": "CA",
  "confidence": "default_only"
}
```

**Example:**
```python
result = await client.call_tool(
    "get_default_state_from_ip",
    arguments={"ip": "8.8.8.8"}
)
```

### 2. search_cases

Search case law using CourtListener API.

**Parameters:**
- `query` (str): Legal search query
- `state` (str): State code ("CA", "NY") or "federal" or "nationwide"
- `mode` (str, optional): "semantic" or "keyword" (default: "semantic")

**Returns:**
```json
[
  {
    "case_name": "Smith v. Jones",
    "court": "Supreme Court of California",
    "date": "2023-05-15",
    "citation": "123 Cal. 4th 567",
    "snippet": "...",
    "url": "https://...",
    "raw_score": 0.85
  }
]
```

**Example:**
```python
result = await client.call_tool(
    "search_cases",
    arguments={
        "query": "contract formation text message",
        "state": "CA",
        "mode": "semantic"
    }
)
```

### 3. search_bills

Search state legislation using Open States API.

**Parameters:**
- `query` (str): Legislative search query
- `state` (str): Two-letter state code (e.g., "CA", "OR")

**Returns:**
```json
[
  {
    "bill_id": "AB 1234",
    "title": "Electronic Signatures Act",
    "state": "California",
    "session": "2023-2024",
    "url": "https://...",
    "latest_action": "Passed Assembly",
    "latest_action_date": "2023-06-10",
    "status": ["bill"]
  }
]
```

**Example:**
```python
result = await client.call_tool(
    "search_bills",
    arguments={
        "query": "electronic signatures",
        "state": "CA"
    }
)
```

## Test Client

A comprehensive test client is provided at `MCP/test_client.py`.

### Running the Test Client

1. Start the MCP server:
```bash
npm run dev:mcp
```

2. In another terminal, run the test client:
```bash
cd MCP
python test_client.py
```

The test client will:
- Connect to the MCP server via Streamable HTTP
- List all available tools
- Test each tool with realistic legal research queries
- Display formatted results

### Test Client Output

```
================================================================================
Legal Research MCP - Test Client
================================================================================

Connecting to MCP server at http://localhost:8001/mcp...
✓ Connected successfully

--------------------------------------------------------------------------------
AVAILABLE TOOLS
--------------------------------------------------------------------------------
1. get_default_state_from_ip
   Description: Infer default US state from IP address...
   
2. search_cases
   Description: Search case law using CourtListener API...
   
3. search_bills
   Description: Search state legislation using Open States API...
```

## Client Integration

### Python Client

```python
import asyncio
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

async def main():
    transport = StreamableHttpTransport(url="http://localhost:8001/mcp")
    
    async with Client(transport) as client:
        # List available tools
        tools = await client.list_tools()
        
        # Call a tool
        result = await client.call_tool(
            "get_default_state_from_ip",
            arguments={"ip": "8.8.8.8"}
        )
        print(result.content[0].text)

asyncio.run(main())
```

### Backend Integration

The Backend service can integrate with MCP tools using the FastMCP client:

```python
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

# In your LangChain tool wrapper
mcp_client = Client(
    StreamableHttpTransport(url="http://localhost:8001/mcp")
)

# Call MCP tools from LangChain chains
async def search_cases_tool(query: str, state: str):
    result = await mcp_client.call_tool(
        "search_cases",
        arguments={"query": query, "state": state, "mode": "semantic"}
    )
    return json.loads(result.content[0].text)
```

## Configuration

All configuration is in `MCP/.env`:

```bash
# External API Keys
COURTLISTENER_API_KEY=your_key_here
OPEN_STATES_API_KEY=your_key_here
IPINFO_TOKEN=your_token_here

# Service Configuration
MCP_PORT=8001
MCP_CASE_RESULT_LIMIT=10
MCP_DOC_TEXT_CHAR_LIMIT=6000
```

## Error Handling

Tools return structured error responses on failure:

```json
{
  "country": "US",
  "state": null,
  "state_code": null,
  "confidence": "error",
  "error": "IPinfo request timed out after 10s"
}
```

For case/bill searches, errors are returned as single-item arrays:

```json
[
  {
    "case_name": "Error",
    "snippet": "CourtListener search failed: ...",
    ...
  }
]
```

## Troubleshooting

### Server won't start

1. Check that fastmcp is installed: `pip install fastmcp>=3.0.0`
2. Verify API keys are set in `MCP/.env`
3. Check port 8001 is not already in use

### Test client can't connect

1. Ensure MCP server is running
2. Check the URL: `http://localhost:8001/mcp` (note the `/mcp` path)
3. Verify no firewall blocking localhost:8001

### Tool calls timeout

1. External APIs (CourtListener, Open States, IPinfo) have rate limits
2. Check network connectivity
3. Verify API keys are valid and not expired

## Differences from REST API

The FastMCP implementation differs from a traditional REST API:

- **Protocol**: MCP protocol over Streamable HTTP (SSE), not REST
- **Endpoint**: Single `/mcp` endpoint, not multiple REST routes
- **Communication**: Tools are invoked via MCP protocol, not HTTP methods
- **Client**: Must use FastMCP client or MCP-compatible client
- **Transport**: Streamable HTTP supports bidirectional streaming

## Next Steps

- Integrate with Backend service using FastMCP client
- Add more tools for document extraction
- Implement tool-level caching for repeated queries
- Add tool result metadata for better observability
