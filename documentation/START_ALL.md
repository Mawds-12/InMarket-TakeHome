# Combined Startup Guide — Precedent Brief

Instructions for running all three services (MCP, Backend, Frontend) simultaneously.

---

## Prerequisites

Before starting any services, ensure you have:

| Requirement | Version | Check Command |
|------------|---------|---------------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

---

## Step 1 — Configure Environment Variables

Each service needs its own `.env` file. Copy the `.env.example` file in each service folder and fill in your API keys.

### MCP Service
```bash
cd MCP
cp .env.example .env
# Edit MCP/.env and add your API keys:
# - COURTLISTENER_API_KEY
# - OPEN_STATES_API_KEY
# - IPINFO_TOKEN
```

### Backend Service
```bash
cd Backend
cp .env.example .env
# Edit Backend/.env and add:
# - ANTHROPIC_API_KEY
```

### Frontend Service
```bash
cd FrontEnd
cp .env.example .env.local
# Edit FrontEnd/.env.local (optional - defaults work for local dev)
```

---

## Step 2 — Install Dependencies

### Install Root Dependencies (for combined startup)
```bash
# From project root
npm install
```

### Install MCP Dependencies
```bash
cd MCP
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
cd ..
```

### Install Backend Dependencies
```bash
cd Backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
cd ..
```

### Install Frontend Dependencies
```bash
cd FrontEnd
npm install
cd ..
```

---

## Step 3 — Start All Services

### Option 1: Automated Startup (Recommended)

From the project root, run:

```bash
npm run dev
```

This starts all three services in parallel with colored output:
- **[MCP]** — Cyan — Port 8001
- **[Backend]** — Magenta — Port 8000
- **[Frontend]** — Green — Port 3000

Press `Ctrl+C` to stop all services.

### Option 2: Manual Startup (Three Terminals)

**Terminal 1 — MCP Service:**
```bash
cd MCP
# Activate venv first (see Step 2)
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 — Backend Service:**
```bash
cd Backend
# Activate venv first (see Step 2)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3 — Frontend:**
```bash
cd FrontEnd
npm run dev
```

---

## Step 4 — Verify Services

### MCP Service (Port 8001)
```bash
curl http://localhost:8001/health
# Expected: {"status":"ok","service":"mcp","port":8001}
```

### Backend Service (Port 8000)
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"backend","port":8000,"mcp_url":"http://localhost:8001"}
```

### Frontend (Port 3000)
Open http://localhost:3000 in your browser.
You should see the Precedent Brief homepage.

---

## Port Reference

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend | 8000 | http://localhost:8000 |
| MCP | 8001 | http://localhost:8001 |

---

## Individual Service Scripts

Run individual services without starting all three:

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

### "Module not found" errors
- Ensure you've run `pip install -r requirements.txt` in the MCP and Backend folders
- Ensure you've run `npm install` in the FrontEnd folder and project root
- Verify your virtual environment is activated for Python services

### "Connection refused" on port 8000 or 8001
- Check that the relevant service is running
- Verify the port isn't already in use by another process
- Check the `.env` file has the correct port configuration

### Missing API keys
- Verify all required keys are set in the appropriate `.env` files
- MCP needs: COURTLISTENER_API_KEY, OPEN_STATES_API_KEY, IPINFO_TOKEN
- Backend needs: ANTHROPIC_API_KEY
- Never commit `.env` files to git

### Python version issues
- This project requires Python 3.11 or higher
- Use `pyenv` or similar to manage Python versions if needed

### uvicorn command not found
- Ensure your virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`

---

## Next Steps

Once all services are running:
1. The Frontend will be available at http://localhost:3000
2. API documentation available at:
   - Backend: http://localhost:8000/docs
   - MCP: http://localhost:8001/docs
3. Continue with component implementation as outlined in the project documentation
