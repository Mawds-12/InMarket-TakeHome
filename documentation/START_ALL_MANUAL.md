# Startup Guide — Precedent Brief

**Prerequisites:** Python 3.11+, Node.js 18+, npm 9+

> This guide assumes **Windows**. Mac/Linux config is at the bottom.

---

## 1 — Environment Variables

Copy each example file and fill in your API keys.

```bash
copy MCP\.env.example MCP\.env
copy Backend\.env.example Backend\.env
copy FrontEnd\.env.example FrontEnd\.env.local
```

| File | Keys needed |
|------|-------------|
| `MCP\.env` | `COURTLISTENER_API_KEY`, `OPEN_STATES_API_KEY`, `IPINFO_TOKEN` |
| `Backend\.env` | `ANTHROPIC_API_KEY` |
| `FrontEnd\.env.local` | Defaults work for local dev — no changes needed |

---

## 2 — Install Dependencies

```bash
# Root (concurrently runner)
npm install

# Python dependencies (shared venv for MCP and Backend)
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd FrontEnd && npm install && cd ..
```

**Note:** You can skip manual installation! Running `npm run dev` will automatically install all dependencies if they're missing.

---

## 3 — Start

```bash
npm run dev
```

This single command will:
- Copy `.env.example` files to `.env` if they don't exist
- Install Python dependencies in a shared venv if needed
- Install Frontend dependencies if needed
- Start all three services in parallel

Open http://localhost:3000 once all services are running.

| Service | Port |
|---------|------|
| Frontend | 3000 |
| Backend | 8000 |
| MCP | 8001 |

To run services individually: `npm run dev:frontend`, `npm run dev:backend`, `npm run dev:mcp`

---

## How `npm run dev` works

The root `package.json` uses `concurrently` to spawn all three services as parallel processes
in one terminal. Each service gets a color-coded prefix so output stays readable.

**Unified Virtual Environment:**
- A single `venv/` at the project root is shared by both MCP and Backend services
- All Python dependencies are in one `requirements.txt` at the root
- The venv's `uvicorn.exe` is called directly by path — no activation needed in npm scripts

```json
{
  "scripts": {
    "predev": "npm run setup:env && (npm run setup:check || (npm run setup:python && npm run setup:frontend))",
    "dev": "concurrently --names MCP,Backend,Frontend --prefix-colors cyan,magenta,green \"npm run dev:mcp\" \"npm run dev:backend\" \"npm run dev:frontend\"",
    "dev:mcp":      "cd MCP && ..\\venv\\Scripts\\uvicorn.exe main:app --host 0.0.0.0 --port 8001 --reload",
    "dev:backend":  "cd Backend && ..\\venv\\Scripts\\uvicorn.exe main:app --host 0.0.0.0 --port 8000 --reload",
    "dev:frontend": "cd FrontEnd && npm run dev"
  },
  "devDependencies": {
    "concurrently": "^8.0.0"
  }
}
```

The `predev` script automatically runs before `dev` to ensure all dependencies are installed.

---

## Troubleshooting

**Port already in use** — another process is on that port. Kill it or change the port in the relevant `.env` file.

**`uvicorn` not found** — venv wasn't created or `pip install` didn't complete. Run `npm run setup:python` manually.

**`Connection refused` on 8000 or 8001** — the service didn't start cleanly. Check the terminal output for errors, usually a missing API key in `.env`.

**API key errors** — confirm keys are in the correct `.env` file. MCP keys in `MCP\.env`, Anthropic key in `Backend\.env` only.

---

## Mac / Linux Config

Everything is the same except:

**Step 1 — copy commands:**
```bash
cp MCP/.env.example MCP/.env
cp Backend/.env.example Backend/.env
cp FrontEnd/.env.example FrontEnd/.env.local
```

**Step 2 — venv activation:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd FrontEnd && npm install && cd ..
```

**package.json scripts** — use forward slashes:
```json
"dev:mcp":     "cd MCP && ../venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001 --reload",
"dev:backend": "cd Backend && ../venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
```