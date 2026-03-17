# Precedent Brief
### AI-Powered Legal Research Triage App

A structured legal research tool — not a chatbot. The user enters a plain-English legal question,
optionally pastes a contract clause, and the system returns only the most pertinent case law and
legislative context in simple language.

---

## Project Structure

```
precedent-brief/
├── README.md                   ← You are here
├── documentation/
│   ├── ARCHITECTURE.md         ← System design, data flow, layer responsibilities
│   ├── STARTUP_GUIDE.md        ← How to run the full stack locally
│   ├── API_CONTRACTS.md        ← All internal endpoint shapes (request + response)
│   └── ENV_REFERENCE.md        ← Every environment variable, what it does, where it goes
├── MCP/                        ← Wrapper microservice (FastAPI)
│   ├── README.md               ← MCP-specific setup and endpoint guide
│   ├── requirements.txt
│   └── ...
├── Backend/                    ← LLM agent + LangChain orchestration (FastAPI)
│   ├── README.md               ← Backend-specific setup and chain guide
│   ├── requirements.txt
│   └── ...
└── FrontEnd/                   ← Next.js single-page research workspace
    ├── README.md               ← Frontend-specific setup guide
    ├── package.json
    └── ...
```

---

## What This App Does

1. User submits a legal question + optional clause text + jurisdiction choice
2. Server infers a default state from request IP (always user-editable)
3. LLM extracts a structured **issue bundle** from the question
4. LangChain orchestrates parallel calls to CourtListener (cases) and Open States (bills)
5. A relevance reducer drops anything not materially connected to the issue
6. LLM writes a compact **precedent brief** using only the surviving evidence

**This is a research triage system, not a legal advice engine.**

---

## Tech Stack

| Layer       | Technology                          | Purpose                                  |
|-------------|-------------------------------------|------------------------------------------|
| Frontend    | Next.js (React)                     | Structured form + results workspace     |
| Backend     | FastAPI + LangChain                 | LLM orchestration, issue extraction, brief writing |
| MCP Service | FastAPI                             | Thin wrapper over external APIs          |
| Case law    | CourtListener API                   | Keyword + semantic search over opinions  |
| Legislation | Open States API v3                  | State bill and legislative activity      |
| Geolocation | IPinfo API                          | Default state inference from request IP  |
| LLM         | Claude (Anthropic) via LangChain    | Issue extraction, reduction, brief writing |

---

## Quick Start

See `documentation/STARTUP_GUIDE.md` for the full local setup walkthrough.

Short version:
```bash
# 1. Start MCP wrapper service
cd MCP && pip install -r requirements.txt && uvicorn main:app --port 8001

# 2. Start LLM backend
cd Backend && pip install -r requirements.txt && uvicorn main:app --port 8000

# 3. Start frontend
cd FrontEnd && npm install && npm run dev
```

Frontend runs at: http://localhost:3000
Backend runs at:  http://localhost:8000
MCP service runs at: http://localhost:8001

---

## Key Design Decisions

**Why a form, not a chatbot?**
A structured form enforces disciplined issue extraction and makes output scorable. Chatbots
encourage weak retrieval and irrelevant output.

**Why is IP state inference editable?**
VPNs, proxies, mobile carriers, and corporate networks skew geolocation. A legal question may
also concern a different state than the user's location. The inferred state is a convenience
default, never an assumption.

**Why a pertinence reducer?**
Raw legal API results are noisy. A second model pass scores each result against the extracted
issue bundle and drops anything that doesn't materially connect. This is what makes the app
feel intelligent.

**Why LangChain?**
Not for autonomous agent behavior — for controlled orchestration. LangChain manages the
issue-extraction → tool-call → reduction → brief-writing chain with predictable structure.

---

## Not Legal Advice

This application is a legal research triage tool. It identifies issues and surfaces relevant
authorities. It does not constitute legal advice and should not be relied upon as such.