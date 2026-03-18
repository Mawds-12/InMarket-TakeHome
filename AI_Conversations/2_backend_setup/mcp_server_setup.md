User: Please reference MCP documentation and general documentation as needed, if you 
are unsure do not implement and ask questions. Follow the architecture provided 
thoroughly and accurately.
Create a test client script in the MCP folder that connects to the running MCP server 
over Streamable HTTP. The script should list all available tools, then call each tool 
with realistic stub inputs and print the results. Use the FastMCP client library which 
handles the transport automatically when given the server URL.

---

Model: After reviewing the MCP folder and documentation, I found a significant 
mismatch between your request and the current implementation.

Current Implementation:
- The MCP service is a standard FastAPI REST API (not using FastMCP framework)
- Uses regular HTTP endpoints: /geo/*, /cases/*, /bills/*
- No FastMCP library in requirements.txt
- No Model Context Protocol (MCP) framework detected

Your Request mentions:
- FastMCP client library
- Streamable HTTP transport
- Listing "tools" (MCP terminology)

Critical Questions:
1. Framework Choice:
   Option A: Test the existing FastAPI service with regular httpx client?
   Option B: Convert to FastMCP framework first, then create the test client?

2. Missing Implementations: The routers folder is currently empty. Should I:
   - Implement the missing routers first?
   - Create test stubs assuming they'll exist?
   - Only test currently working endpoints (/health, /)?

3. Test Data: Should I infer realistic test data from the documentation, or do you 
   have specific test cases in mind?

---

User: Option B this must be a FASTMCP framework exclusively, this is not a rest 
endpoint

---

Model: I understand - this must be converted to FastMCP framework exclusively. 
Researched FastMCP docs and updated the plan.

Phase 1: Convert to FastMCP Framework
- Replace FastAPI with FastMCP library
- Convert REST endpoints → MCP tools using @mcp.tool decorator
- Implement missing clients (IPinfo, CourtListener, Open States)
- Implement normalizers for clean data schemas
- Use Streamable HTTP transport on port 8001

Phase 2: Create Test Client
- Use StreamableHttpTransport to connect to http://localhost:8001/mcp
- List all available tools
- Call each tool with realistic legal research test data
- Pretty-print results

Tools to Implement:
- get_default_state_from_ip - IP geolocation
- search_cases - CourtListener case law search
- search_bills - Open States legislation search
- extract_document_text - Document text extraction (optional)

Questions before proceeding:
1. All 4 tools or core 3? (geo, cases, bills vs. include document extraction)
2. Error handling: Return error dicts or raise exceptions?
3. API keys: Keep reading from config.py settings, correct?
4. Test output: Console output with JSON or save to files?
5. Backend compatibility: Fully convert to MCP protocol (Backend would need FastMCP 
   client too)?