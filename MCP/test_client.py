# test_client.py
#
# Test client for the Legal Research MCP service.
# Connects via Streamable HTTP transport, lists tools, and tests each with realistic data.

import asyncio
import json
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


async def main():
    """Main test client execution."""
    print("=" * 80)
    print("Legal Research MCP - Test Client")
    print("=" * 80)
    print()
    
    # Connect to MCP server
    print("Connecting to MCP server at http://localhost:8001/mcp...")
    transport = StreamableHttpTransport(url="http://localhost:8001/mcp")
    
    async with Client(transport) as client:
        print("✓ Connected successfully\n")
        
        # List all available tools
        print("-" * 80)
        print("AVAILABLE TOOLS")
        print("-" * 80)
        
        tools = await client.list_tools()
        for i, tool in enumerate(tools.tools, 1):
            print(f"{i}. {tool.name}")
            print(f"   Description: {tool.description}")
            if tool.inputSchema:
                print(f"   Parameters: {list(tool.inputSchema.get('properties', {}).keys())}")
            print()
        
        # Test 1: IP Geolocation
        print("-" * 80)
        print("TEST 1: Get Default State from IP")
        print("-" * 80)
        
        test_ips = [
            ("8.8.8.8", "Google DNS - should return California"),
            ("1.1.1.1", "Cloudflare DNS - may vary")
        ]
        
        for ip, description in test_ips:
            print(f"\nTesting IP: {ip} ({description})")
            try:
                result = await client.call_tool(
                    "get_default_state_from_ip",
                    arguments={"ip": ip}
                )
                print("Result:")
                print(json.dumps(result.content[0].text if result.content else {}, indent=2))
            except Exception as e:
                print(f"Error: {str(e)}")
        
        # Test 2: Case Law Search
        print("\n" + "-" * 80)
        print("TEST 2: Search Cases")
        print("-" * 80)
        
        case_queries = [
            {
                "query": "contract formation text message",
                "state": "CA",
                "mode": "semantic",
                "description": "Semantic search for text message contracts in California"
            },
            {
                "query": "consideration acceptance offer",
                "state": "NY",
                "mode": "keyword",
                "description": "Keyword search for contract basics in New York"
            }
        ]
        
        for test in case_queries:
            print(f"\nQuery: {test['description']}")
            print(f"Parameters: query='{test['query']}', state={test['state']}, mode={test['mode']}")
            try:
                result = await client.call_tool(
                    "search_cases",
                    arguments={
                        "query": test["query"],
                        "state": test["state"],
                        "mode": test["mode"]
                    }
                )
                cases = json.loads(result.content[0].text) if result.content else []
                print(f"Found {len(cases)} cases")
                
                if cases and len(cases) > 0:
                    print("\nTop result:")
                    top_case = cases[0]
                    print(f"  Case: {top_case.get('case_name', 'N/A')}")
                    print(f"  Court: {top_case.get('court', 'N/A')}")
                    print(f"  Date: {top_case.get('date', 'N/A')}")
                    print(f"  Citation: {top_case.get('citation', 'N/A')}")
                    print(f"  Score: {top_case.get('raw_score', 0.0):.2f}")
                    snippet = top_case.get('snippet', '')
                    if snippet:
                        print(f"  Snippet: {snippet[:150]}...")
            except Exception as e:
                print(f"Error: {str(e)}")
        
        # Test 3: Legislative Search
        print("\n" + "-" * 80)
        print("TEST 3: Search Bills")
        print("-" * 80)
        
        bill_queries = [
            {
                "query": "electronic signatures",
                "state": "CA",
                "description": "Electronic signature laws in California"
            },
            {
                "query": "consumer protection data privacy",
                "state": "OR",
                "description": "Data privacy legislation in Oregon"
            }
        ]
        
        for test in bill_queries:
            print(f"\nQuery: {test['description']}")
            print(f"Parameters: query='{test['query']}', state={test['state']}")
            try:
                result = await client.call_tool(
                    "search_bills",
                    arguments={
                        "query": test["query"],
                        "state": test["state"]
                    }
                )
                bills = json.loads(result.content[0].text) if result.content else []
                print(f"Found {len(bills)} bills")
                
                if bills and len(bills) > 0:
                    print("\nTop result:")
                    top_bill = bills[0]
                    print(f"  Bill ID: {top_bill.get('bill_id', 'N/A')}")
                    print(f"  Title: {top_bill.get('title', 'N/A')[:100]}...")
                    print(f"  State: {top_bill.get('state', 'N/A')}")
                    print(f"  Session: {top_bill.get('session', 'N/A')}")
                    print(f"  Latest Action: {top_bill.get('latest_action', 'N/A')[:80]}...")
                    print(f"  Date: {top_bill.get('latest_action_date', 'N/A')}")
            except Exception as e:
                print(f"Error: {str(e)}")
        
        print("\n" + "=" * 80)
        print("Test client completed successfully")
        print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nFatal error: {str(e)}")
        import traceback
        traceback.print_exc()
