# Architecture — Precedent Brief

## Overview

Four layers with strict separation of concerns. Each layer has one job and talks to the next
layer through a defined contract. No layer reaches past its neighbor.

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│   Next.js — structured research form + results workspace    │
│   Talks to: Backend only (port 8000)                        │
└──────────────────────────┬──────────────────────────────────┘
                           │  HTTP (JSON)
┌──────────────────────────▼──────────────────────────────────┐
│                        BACKEND                              │
│   FastAPI + LangChain — LLM orchestration                   │
│   Responsibilities:                                         │
│     • Receive user question + facts + state                 │
│     • Call MCP to infer default state from IP               │
│     • Run issue extraction LLM chain                        │
│     • Call MCP tools in parallel (cases + bills)            │
│     • Run relevance reduction LLM chain                     │
│     • Run final brief-writing LLM chain                     │
│     • Return structured brief JSON to frontend              │
│   Talks to: MCP service only (port 8001)                    │
│   Holds: LLM API key (never exposed to frontend or MCP)     │
└──────────────────────────┬──────────────────────────────────┘
                           │  HTTP (JSON)
┌──────────────────────────▼──────────────────────────────────┐
│                      MCP SERVICE                            │
│   FastAPI — thin deterministic wrapper                      │
│   Responsibilities:                                         │
│     • IP → state lookup (IPinfo)                            │
│     • Case search (CourtListener)                           │
│     • Bill search (Open States)                             │
│     • Document text extraction (optional, MVP)              │
│   Talks to: External APIs only                              │
│   Holds: CourtListener key, Open States key, IPinfo token   │
└──────────────────────────┬──────────────────────────────────┘
                           │  HTTPS
┌──────────────────────────▼──────────────────────────────────┐
│                     PUBLIC APIs                             │
│   CourtListener  /  Open States v3  /  IPinfo               │
└─────────────────────────────────────────────────────────────┘
```

---

## End-to-End Data Flow

```
User submits form
      │
      ▼
POST /api/analyze  (Frontend → Backend)
  body: { question, clause_text, state_override, search_mode }
      │
      ▼
Backend: request IP forwarded in header
      │
      ├─► POST /geo/default-state  (Backend → MCP)
      │       if no state_override provided
      │
      ▼
Backend: LLM chain — Issue Extraction
  input:  question + clause_text + resolved_state
  output: issue_bundle (see schema below)
      │
      ├─► POST /cases/search  (parallel)  (Backend → MCP)
      │       input: issue_bundle.case_query + state + mode
      │
      └─► POST /bills/search  (parallel, if issue_bundle.need_bills)
              input: issue_bundle.bill_query + state
      │
      ▼
Backend: LLM chain — Relevance Reduction
  input:  raw cases + raw bills + issue_bundle
  output: only pertinent authorities (some may be dropped entirely)
      │
      ▼
Backend: LLM chain — Brief Writing
  input:  issue_bundle + pertinent_authorities
  output: brief JSON (see response schema in API_CONTRACTS.md)
      │
      ▼
Response returned to Frontend
Frontend renders: issue summary card, authority cards, considerations, coverage note
```

---

## LangChain Orchestration Chain

The Backend runs a **controlled chain**, not a free-form autonomous agent.
Each stage has fixed inputs and fixed output schemas.

```
Stage A — Issue Extraction
  Model: Claude
  Input:  { question, clause_text, state }
  Output: IssueBundle (structured JSON — see below)
  Why:    Converts vague question into precise search terms and identifies
          what facts would change the legal outcome

Stage B — Retrieval (parallel tool calls via LangChain tools)
  Tool 1: search_cases(query, state, mode) → raw case list
  Tool 2: search_bills(query, state)       → raw bill list (if need_bills=true)
  Why:    LangChain tool-calling gives clean separation between the LLM
          deciding what to search and the MCP service executing the search

Stage C — Relevance Reduction
  Model: Claude
  Input:  { issue_bundle, raw_cases, raw_bills }
  Output: List of pertinent authorities only, each with why_pertinent populated
  Why:    Raw legal search is noisy. This stage is what makes the app
          appear discerning rather than just a search passthrough

Stage D — Brief Writing
  Model: Claude
  Input:  { issue_bundle, pertinent_authorities }
  Output: Final brief JSON (issue_summary, authorities, considerations, coverage_note)
  Why:    Shapes the reduced evidence into a readable, structured brief
          constrained to the fixed output schema — no free-form chat
```

---

## Issue Bundle Schema

Output of Stage A. Drives all downstream retrieval and ranking.

```json
{
  "issue_label": "text message contract enforceability",
  "topic_tags": ["contract formation", "payment dispute", "website services"],
  "case_query": "text message agreement contract enforceable services payment",
  "bill_query": "electronic contracts digital signatures",
  "fact_sensitive_points": [
    "Was there clear acceptance?",
    "Were price and scope definite?",
    "Did performance begin?"
  ],
  "need_bills": true
}
```

---

## Final Brief Response Schema

```json
{
  "issue_summary": "string — simple-language framing of the detected legal issue",
  "jurisdiction_used": "OR",
  "state_was_inferred": true,
  "pertinent_authorities": [
    {
      "kind": "case | bill",
      "title": "string",
      "citation": "string (cases only)",
      "court": "string (cases only)",
      "date": "string",
      "url": "string",
      "why_pertinent": "string — ties this authority to the user's specific facts",
      "key_point": "string — the holding or provision that matters"
    }
  ],
  "fact_sensitive_considerations": ["string"],
  "coverage_note": "string — what was searched, what was excluded, any uncertainty"
}
```

---

## Security Model

| Secret              | Lives In          | Never In                        |
|---------------------|-------------------|---------------------------------|
| Anthropic API key   | Backend .env      | Frontend, MCP, git repository   |
| CourtListener key   | MCP .env          | Backend, Frontend, git          |
| Open States key     | MCP .env          | Backend, Frontend, git          |
| IPinfo token        | MCP .env          | Backend, Frontend, git          |

All `.env` files are `.gitignore`d. See `documentation/ENV_REFERENCE.md` for the full list
of required variables per service.

The MCP service is **not publicly exposed** — it is an internal service called only by the
Backend. In production, it should not be routable from the internet.

---

## Deployment Overview (Verbal/Conceptual)

**Local dev:** Three processes (frontend, backend, MCP) on three ports, coordinated manually
or via a tool like `concurrently` or a `Makefile`.

**Containerized:** One Dockerfile per service. A `docker-compose.yml` at the project root
brings up all three with correct port mapping and shared `.env` injection. The MCP container
is on an internal Docker network only — not mapped to a host port.

**Serverless/cloud:** Frontend → Vercel (Next.js native). Backend + MCP → separate Railway,
Render, or AWS Lambda deployments. MCP URL is injected into Backend as an env var. Request
IP is read from the `x-forwarded-for` header, which Vercel, Railway, and similar platforms
populate automatically.

**Kubernetes (advanced):** Frontend as a Deployment + Ingress. Backend and MCP as internal
Deployments with ClusterIP Services (no external exposure for MCP). Secrets managed via
Kubernetes Secrets or a vault integration.