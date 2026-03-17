# Environment Variable Reference — Precedent Brief

Every environment variable used across the project. One source of truth.
Copy the block for each service into that service's `.env` file.

---

## MCP Service — /MCP/.env

```env
# ── External API Keys ──────────────────────────────────────────────────────────

# CourtListener API key
# Get it at: https://www.courtlistener.com/help/api/
# Used in: Authorization: Token <value> header on every CourtListener request
COURTLISTENER_API_KEY=

# Open States API v3 key
# Get it at: https://openstates.org/accounts/register/
# Used in: X-API-Key header on every Open States request
OPEN_STATES_API_KEY=

# IPinfo access token
# Get it at: https://ipinfo.io/signup
# Free tier: 50,000 req/month
# Used in: ?token=<value> query param on geolocation requests
IPINFO_TOKEN=

# ── Service Configuration ──────────────────────────────────────────────────────

# Port the MCP service listens on
MCP_PORT=8001

# Maximum number of raw case results to return before reduction
# Reducer in Backend will trim further. 10 is a safe cap.
MCP_CASE_RESULT_LIMIT=10

# Maximum characters to return from document text extraction
# Prevents oversized LLM prompts downstream
MCP_DOC_TEXT_CHAR_LIMIT=6000
```

---

## Backend — /Backend/.env

```env
# ── LLM ────────────────────────────────────────────────────────────────────────

# Anthropic API key
# Get it at: https://console.anthropic.com/
# NEVER put this in MCP or Frontend
ANTHROPIC_API_KEY=

# Claude model to use for all LLM chains
# Recommended: claude-sonnet-4-20250514 (good balance of speed and quality)
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# ── Internal Services ──────────────────────────────────────────────────────────

# Base URL of the MCP wrapper service
# In local dev: http://localhost:8001
# In Docker: http://mcp:8001  (use the Docker service name)
# In production: set to the internal network URL — do not expose MCP publicly
MCP_BASE_URL=http://localhost:8001

# ── Service Configuration ──────────────────────────────────────────────────────

BACKEND_PORT=8000

# LangChain is an open-source library installed via pip — it requires no API key.
```

---

## Frontend — /FrontEnd/.env.local

```env
# ── Backend Connection ─────────────────────────────────────────────────────────

# URL of the Backend service
# In local dev: http://localhost:8000
# In production: set to your deployed backend URL
# This is used by Next.js API routes (server-side), not directly in the browser
BACKEND_URL=http://localhost:8000

# ── Feature Flags (optional) ───────────────────────────────────────────────────

# Show the "debug: view dropped results" toggle in the UI
# Set to "true" during development, "false" for demo mode
NEXT_PUBLIC_SHOW_DEBUG_TOGGLE=false
```

---

## .gitignore additions (add to project root)

```gitignore
# Environment files — never commit
MCP/.env
Backend/.env
FrontEnd/.env.local

# Python virtual environments
MCP/venv/
Backend/venv/

# Node modules
FrontEnd/node_modules/
FrontEnd/.next/

# General
.DS_Store
__pycache__/
*.pyc
*.pyo
.pytest_cache/
```

---

## .env.example files (commit these — no real values)

Each service folder should contain a `.env.example` with all keys present but values blank.
New developers copy the example and fill in their own keys.

**/MCP/.env.example**
```env
COURTLISTENER_API_KEY=
OPEN_STATES_API_KEY=
IPINFO_TOKEN=
MCP_PORT=8001
MCP_CASE_RESULT_LIMIT=10
MCP_DOC_TEXT_CHAR_LIMIT=6000
```

**/Backend/.env.example**
```env
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-20250514
MCP_BASE_URL=http://localhost:8001
BACKEND_PORT=8000
```

**/FrontEnd/.env.example** (rename to `.env.local`)
```env
BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_SHOW_DEBUG_TOGGLE=false
```