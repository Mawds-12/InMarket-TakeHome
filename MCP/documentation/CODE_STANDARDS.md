# Code Standards — MCP Service

This service is a thin, deterministic wrapper over external APIs.
It normalizes messy third-party responses into clean internal shapes.
It contains no LLM logic and makes no decisions about relevance.

---

## Core Philosophy

The MCP service should be boring. Every function does one thing.
Every file handles one resource or one external API.
If something surprising is happening, a comment explains why.
If the code is self-evident, it speaks for itself.

---

## File Header Block

Required at the top of every file. Omit any field that has nothing useful to say.

```python
# clients/courtlistener.py
#
# HTTP client for the CourtListener search API.
# All requests use token-based auth read from settings.
#
# Raises: CourtListenerError on non-200 responses or network timeouts.
```

```python
# normalizers/case_normalizer.py
#
# Converts raw CourtListener opinion results into the internal Case schema.
# Only the fields used downstream are extracted; all others are discarded.
```

```python
# routers/cases.py
#
# Route handler for POST /cases/search.
# Delegates to the CourtListener client and case normalizer.
```

If the file's purpose is obvious from its name and location (e.g., `config.py`,
`exceptions.py`), keep the header to one line.

---

## Inline Comments

Only add a comment when the code cannot explain itself.

```python
# BAD — narrates the code
results.sort(key=lambda r: r.raw_score, reverse=True)  # sort by score descending

# GOOD — explains a non-obvious constraint
# Cap at the configured limit before returning. The Backend's reducer needs
# raw_score to rank further, but unbounded results cause token bloat.
results = sorted(results, key=lambda r: r.raw_score, reverse=True)[:settings.mcp_case_result_limit]
```

Never comment:
- What a clearly named variable holds
- What a clearly named function does
- Closing braces or blocks
- Disabled code — delete it, git has history

---

## Folder Structure

```
MCP/
├── main.py               ← App entry, router registration only
├── config.py             ← Settings loaded from .env
├── exceptions.py         ← One custom exception class per external service
├── routers/
│   ├── geo.py            ← POST /geo/default-state
│   ├── cases.py          ← POST /cases/search
│   ├── bills.py          ← POST /bills/search
│   └── documents.py      ← POST /documents/extract-text
├── clients/
│   ├── courtlistener.py  ← Raw HTTP calls to CourtListener
│   ├── openstates.py     ← Raw HTTP calls to Open States
│   └── ipinfo.py         ← Raw HTTP calls to IPinfo
├── normalizers/
│   ├── case_normalizer.py   ← Raw CL response → internal Case schema
│   └── bill_normalizer.py   ← Raw OS response → internal Bill schema
└── models/
    ├── requests.py       ← Inbound Pydantic models
    └── responses.py      ← Outbound Pydantic models
```

One file, one concern. When a file starts doing two things, split it.

---

## main.py

Registers routers. Nothing else.

```python
# main.py
#
# FastAPI application entry point for the MCP wrapper service.

from fastapi import FastAPI
from routers import geo, cases, bills, documents

app = FastAPI(title="Precedent Brief — MCP Service")

app.include_router(geo.router)
app.include_router(cases.router)
app.include_router(bills.router)
app.include_router(documents.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mcp"}
```

---

## config.py

All environment variables in one place. Never call `os.getenv()` in business logic.

```python
# config.py
#
# Application settings loaded from environment variables.
# Import `settings` wherever config values are needed.

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    courtlistener_api_key: str
    open_states_api_key: str
    ipinfo_token: str
    mcp_port: int = 8001
    mcp_case_result_limit: int = 10
    mcp_doc_text_char_limit: int = 6000

    class Config:
        env_file = ".env"


settings = Settings()
```

---

## exceptions.py

One exception class per external service. Catch third-party errors in the client
layer and re-raise as these so the router layer stays clean.

```python
# exceptions.py
#
# Custom exceptions for external service failures.
# Raised in client modules; caught in routers to return clean HTTP errors.


class CourtListenerError(Exception):
    pass


class OpenStatesError(Exception):
    pass


class IPInfoError(Exception):
    pass
```

---

## Routers

The router receives, delegates, and returns. No business logic lives here.
Keep each route handler under 10 lines. If it grows, extract to a service module.

```python
# routers/cases.py
#
# Route handler for POST /cases/search.
# Delegates to the CourtListener client and case normalizer.

from fastapi import APIRouter, HTTPException
from clients.courtlistener import search as cl_search
from normalizers.case_normalizer import normalize
from models.requests import CaseSearchRequest
from models.responses import CaseSearchResponse
from exceptions import CourtListenerError

router = APIRouter()


@router.post("/cases/search", response_model=CaseSearchResponse)
async def search_cases(request: CaseSearchRequest) -> CaseSearchResponse:
    try:
        raw = await cl_search(request.query, request.state, request.mode)
    except CourtListenerError as e:
        raise HTTPException(status_code=502, detail=str(e))

    results = normalize(raw["results"])
    return CaseSearchResponse(
        results=results,
        total_found=raw.get("count", len(results)),
        returned=len(results),
    )
```

---

## Clients

Each client file owns all HTTP calls to one external API.
Authenticate, call, check status, return raw response dict. Nothing else.

```python
# clients/courtlistener.py
#
# HTTP client for the CourtListener search API.
# All requests use token-based auth read from settings.
#
# Raises: CourtListenerError on non-200 responses or network timeouts.

import httpx
from config import settings
from exceptions import CourtListenerError

_BASE_URL = "https://www.courtlistener.com/api/rest/v4"
_HEADERS = {"Authorization": f"Token {settings.courtlistener_api_key}"}


async def search(query: str, state: str, mode: str) -> dict:
    params = {"q": query, "type": "o"}
    if state not in ("federal", "nationwide"):
        params["court"] = state.lower()
    if mode == "semantic":
        params["semantic"] = "true"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_BASE_URL}/search/",
                headers=_HEADERS,
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        raise CourtListenerError("CourtListener request timed out")
    except httpx.HTTPStatusError as e:
        raise CourtListenerError(f"CourtListener returned {e.response.status_code}")

    return response.json()
```

---

## Normalizers

Each normalizer converts one type of raw API response into an internal schema.
Private helpers (`_to_case`) do the per-record mapping. The public function maps over them.

```python
# normalizers/case_normalizer.py
#
# Converts raw CourtListener opinion results into the internal Case schema.
# Only the fields used downstream are extracted; all others are discarded.

from models.responses import Case


def normalize(raw_results: list[dict]) -> list[Case]:
    return [_to_case(r) for r in raw_results]


def _to_case(raw: dict) -> Case:
    return Case(
        case_name=raw.get("caseName", "Unknown"),
        court=raw.get("court", ""),
        date=raw.get("dateFiled", ""),
        citation=raw.get("citation", [None])[0],
        snippet=raw.get("snippet", ""),
        url=raw.get("absolute_url", ""),
        raw_score=raw.get("score", 0.0),
    )
```

---

## Models

Split into two files. Keep each file under ~80 lines. Split further if they grow.

```python
# models/requests.py
#
# Pydantic models for inbound MCP request bodies.

from pydantic import BaseModel
from typing import Literal


class CaseSearchRequest(BaseModel):
    query: str
    state: str
    mode: Literal["semantic", "keyword"] = "semantic"


class BillSearchRequest(BaseModel):
    query: str
    state: str


class GeoRequest(BaseModel):
    ip: str
```

```python
# models/responses.py
#
# Pydantic models for outbound MCP response bodies.

from pydantic import BaseModel
from typing import Optional


class Case(BaseModel):
    case_name: str
    court: str
    date: str
    citation: Optional[str]
    snippet: str
    url: str
    raw_score: float


class CaseSearchResponse(BaseModel):
    results: list[Case]
    total_found: int
    returned: int


class GeoResponse(BaseModel):
    country: str
    state: Optional[str]
    state_code: Optional[str]
    # Always "default_only" — this value is a convenience default, never authoritative.
    confidence: str = "default_only"
```

---

## Error Handling

Catch third-party errors in the client. Re-raise as a custom exception.
Let the router convert it to an HTTP error. Never swallow exceptions silently.

```python
# BAD — silent failure
try:
    response = await client.get(url)
except Exception:
    return {}

# GOOD — explicit failure with context
try:
    response = await client.get(url, timeout=10.0)
    response.raise_for_status()
except httpx.TimeoutException:
    raise CourtListenerError("Request timed out after 10s")
except httpx.HTTPStatusError as e:
    raise CourtListenerError(f"Upstream returned {e.response.status_code}")
```

---

## Naming

| Thing | Convention | Example |
|---|---|---|
| Files | `snake_case` | `case_normalizer.py` |
| Functions | `snake_case` | `normalize_cases()` |
| Private helpers | `_snake_case` | `_to_case()` |
| Classes | `PascalCase` | `CourtListenerError` |
| Constants | `SCREAMING_SNAKE_CASE` | `_BASE_URL` |

---

## Function Length

If a function exceeds ~20 lines, ask whether it has a second responsibility.
If it does, extract it. If it genuinely doesn't, keep it together — don't
split a function into artificial pieces just to hit a line count.