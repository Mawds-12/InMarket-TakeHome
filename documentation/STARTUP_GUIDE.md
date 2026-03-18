# Startup Guide — Precedent Brief

Complete instructions for getting all three services running locally from a blank project.
Follow the sections in order on your first setup.

---

## Prerequisites

| Tool        | Required Version | Check Command         |
|-------------|------------------|-----------------------|
| Python      | 3.11+            | `python --version`    |
| Node.js     | 18+              | `node --version`      |
| npm         | 9+               | `npm --version`       |
| Git         | any              | `git --version`       |

Optional but recommended: `pyenv` for Python version management, `nvm` for Node.

---

## Step 1 — Get API Keys

You need four external keys before any service will run. Obtain them first.

### 1a. CourtListener (case law)
- Go to https://www.courtlistener.com/help/api/
- Create a free account
- Generate an API token from your profile page
- Save it as `COURTLISTENER_API_KEY`

### 1b. Open States (state bills)
- Go to https://openstates.org/accounts/register/
- Register for a free account
- Request an API key from your profile
- Save it as `OPEN_STATES_API_KEY`

### 1c. IPinfo (geolocation)
- Go to https://ipinfo.io/signup
- Free tier includes 50,000 requests/month — sufficient for development
- Copy your access token from the dashboard
- Save it as `IPINFO_TOKEN`

### 1d. Anthropic (LLM)
- Go to https://console.anthropic.com/
- Create an account and generate an API key
- Save it as `ANTHROPIC_API_KEY`
- Note: The LLM key goes in the **Backend** only, never in MCP or Frontend

---

## Step 2 — Clone and Set Up the Repo

```bash
git clone <your-repo-url> precedent-brief
cd precedent-brief
```

The project root contains four folders:
```
Documentation/   ← guides and contracts (you are reading one)
MCP/             ← wrapper microservice
Backend/         ← LLM agent
FrontEnd/        ← Next.js app
venv/            ← shared Python virtual environment (created on first run)
requirements.txt ← consolidated Python dependencies
```

---

## Step 3 — Configure Environment Variables

Each service has its own `.env` file. **Never commit these files.**
Each folder contains a `.env.example` file showing required variable names with placeholder values.

### MCP Service (.env)
```
# /MCP/.env

COURTLISTENER_API_KEY=your_key_here
OPEN_STATES_API_KEY=your_key_here
IPINFO_TOKEN=your_token_here

# Service config
MCP_PORT=8001
```

### Backend (.env)
```
# /Backend/.env

ANTHROPIC_API_KEY=your_key_here

# Where the MCP service lives (update if deployed remotely)
MCP_BASE_URL=http://localhost:8001

# Service config
BACKEND_PORT=8000
```

### Frontend (.env.local)
```
# /FrontEnd/.env.local

# Where the backend lives (Next.js server-side env var)
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

> **Note:** `NEXT_PUBLIC_` prefix means Next.js will expose this to the browser.
> Only the backend URL goes here — never API keys.

---

## Step 4 — Install Dependencies

**Automated (Recommended):**
```bash
# From project root
npm install
npm run dev
```
This will automatically copy `.env` files, install Python and Node dependencies, and start all services.

**Manual Installation:**
```bash
# From project root
npm install
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd FrontEnd && npm install && cd ..
```

---

## Step 5 — Start All Services

```bash
# From project root
npm run dev
```

This will start all three services in parallel with color-coded output:
- **[MCP]** (cyan) on port 8001
- **[Backend]** (magenta) on port 8000  
- **[Frontend]** (green) on port 3000

Open http://localhost:3000 in your browser.

You should see the Precedent Brief research workspace with:
- Legal question input
- Jurisdiction selector (auto-detected state shown)
- Optional clause textarea
- Analyze button

---

## Step 6 — Verify Services

**MCP Service:**
```bash
curl http://localhost:8001/health
# Expected: {"status": "ok", "service": "mcp"}
```

**Backend Service:**
```bash
curl http://localhost:8000/health
# Expected: {"status": "ok", "service": "backend"}
```

**Frontend:** Open http://localhost:3000 in your browser.

---

## Running Services Individually (Optional)

If you need to run services separately for debugging:

```bash
# MCP only
npm run dev:mcp

# Backend only
npm run dev:backend

# Frontend only
npm run dev:frontend
```

---

## Troubleshooting

### "Connection refused" on port 8001 or 8000
- Make sure the relevant service is running in another terminal
- Check that you're in the right directory with the right venv activated
- Check the port in your `.env` file matches the port in the `uvicorn` command

### IP geolocation returns wrong state
- This is expected behavior — it's an editable default
- VPNs and corporate networks frequently misreport location
- The frontend state selector lets the user override it

### LLM returns an error about the API key
- Confirm `ANTHROPIC_API_KEY` is set in `/Backend/.env`
- Confirm the key starts with `sk-ant-`
- The LLM key should never be in the MCP or Frontend env files

### Open States returns no results
- Open States has rate limits on free keys
- Confirm `OPEN_STATES_API_KEY` is set in `/MCP/.env`
- For a given issue, `need_bills` may be `false` — no bill call will be made in that case

### CourtListener returns 401
- Confirm `COURTLISTENER_API_KEY` is set correctly
- The header format should be `Authorization: Token <your_key>`

---

## Port Reference

| Service  | Default Port | Config Location           |
|----------|--------------|---------------------------|
| Frontend | 3000         | Next.js default            |
| Backend  | 8000         | `/Backend/.env`            |
| MCP      | 8001         | `/MCP/.env`                |