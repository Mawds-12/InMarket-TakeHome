# Code Standards — Backend

This service owns all LLM orchestration. It extracts issues, calls MCP tools,
reduces results for relevance, and writes the final brief. It holds the only
Anthropic API key in the project and never exposes it.

---

## Core Philosophy

Each LangChain chain is a pipeline with a fixed input and a fixed output.
The Backend is not a free-form agent — it is a controlled orchestrator.
Routers route. Chains chain. Tools call MCP. Prompts live in text files.
No layer reaches past its neighbor.

---

## File Header Block

Required at the top of every file.

```python
# chains/issue_extractor.py
#
# Stage A of the orchestration chain.
# Converts a plain-English legal question into a structured IssueBundle
# used to drive downstream case and bill retrieval.
```

```python
# routers/analyze.py
#
# Route handler for POST /api/analyze.
# Orchestrates the full chain: issue extraction → retrieval → reduction → brief.
```

```python
# tools/case_tool.py
#
# LangChain tool that wraps the MCP /cases/search endpoint.
# Used by the Backend chain to retrieve case law candidates.
```

If the file's purpose is fully obvious from its name (e.g. `config.py`, `exceptions.py`),
one line is enough.

---

## Inline Comments

Add a comment only when the code cannot explain itself.

```python
# BAD — restates the code
results = await asyncio.gather(*tasks)  # run tasks concurrently

# GOOD — explains a structural decision
# Cases and bills are fetched concurrently. Bills are only included when
# need_bills is true in the issue bundle — the task list is built conditionally.
tasks = [fetch_cases(issue_bundle, state)]
if issue_bundle.need_bills and include_bills:
    tasks.append(fetch_bills(issue_bundle, state))
results = await asyncio.gather(*tasks)
```

Never comment:
- What a clearly named variable holds
- What a clearly named function does
- Disabled code — delete it, git has history

---

## Folder Structure

```
Backend/
├── main.py               ← App entry, router registration only
├── config.py             ← Settings from .env
├── exceptions.py         ← LLM and MCP client errors
├── routers/
│   ├── analyze.py        ← POST /api/analyze (main endpoint)
│   └── dev.py            ← POST /api/extract-issue (development/test only)
├── chains/
│   ├── issue_extractor.py    ← Stage A: question → IssueBundle
│   ├── relevance_reducer.py  ← Stage C: raw results → pertinent authorities
│   └── brief_writer.py       ← Stage D: pertinent authorities → BriefResponse
├── tools/
│   ├── case_tool.py      ← Wraps MCP POST /cases/search
│   └── bill_tool.py      ← Wraps MCP POST /bills/search
├── prompts/
│   ├── issue_extraction.txt
│   ├── relevance_reduction.txt
│   └── brief_writing.txt
└── models/
    ├── requests.py       ← Inbound shapes (AnalyzeRequest)
    ├── responses.py      ← Outbound shapes (BriefResponse, Authority)
    └── internal.py       ← Shapes shared between chains (IssueBundle, RawAuthority)
```

---

## main.py

Registers routers. Nothing else.

```python
# main.py
#
# FastAPI application entry point for the Backend service.

from fastapi import FastAPI
from routers import analyze, dev

app = FastAPI(title="Precedent Brief — Backend")

app.include_router(analyze.router)
app.include_router(dev.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "backend"}
```

---

## config.py

One place for all settings. Import `settings` wherever config values are needed.
Never call `os.getenv()` in business logic.

```python
# config.py
#
# Application settings loaded from environment variables.

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-20250514"
    mcp_base_url: str = "http://localhost:8001"
    backend_port: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()
```

---

## Routers

The router receives, orchestrates at a high level, and returns.
It does not contain chain logic, prompt logic, or HTTP client logic.

```python
# routers/analyze.py
#
# Route handler for POST /api/analyze.
# Orchestrates the full chain: issue extraction → retrieval → reduction → brief.

from fastapi import APIRouter, HTTPException, Request
from chains.issue_extractor import extract_issue
from chains.relevance_reducer import reduce_to_pertinent
from chains.brief_writer import write_brief
from tools.case_tool import fetch_cases
from tools.bill_tool import fetch_bills
from models.requests import AnalyzeRequest
from models.responses import BriefResponse
from exceptions import LLMError, MCPError
import asyncio

router = APIRouter()


@router.post("/api/analyze", response_model=BriefResponse)
async def analyze(request: AnalyzeRequest, req: Request) -> BriefResponse:
    try:
        state = request.state_override or await _infer_state(req)
        issue_bundle = await extract_issue(request.question, state, request.clause_text)
        cases, bills = await _run_retrieval(issue_bundle, state, request.include_bills)
        pertinent = await reduce_to_pertinent(issue_bundle, cases, bills)
        return await write_brief(issue_bundle, pertinent, state)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except MCPError as e:
        raise HTTPException(status_code=502, detail=str(e))


async def _infer_state(req: Request) -> str:
    ...


async def _run_retrieval(issue_bundle, state, include_bills):
    tasks = [fetch_cases(issue_bundle, state)]
    if include_bills and issue_bundle.need_bills:
        tasks.append(fetch_bills(issue_bundle, state))
    results = await asyncio.gather(*tasks)
    cases = results[0]
    bills = results[1] if len(results) > 1 else []
    return cases, bills
```

The route handler reads like a sentence. All real work is in the imported modules.

---

## Chains

One file per chain stage. Each file exports one public async function.
All module-level objects (model, prompt, chain) are private constants.

```python
# chains/issue_extractor.py
#
# Stage A of the orchestration chain.
# Converts a plain-English legal question into a structured IssueBundle.

from pathlib import Path
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from models.internal import IssueBundle
from config import settings

_model = ChatAnthropic(
    model=settings.anthropic_model,
    api_key=settings.anthropic_api_key,
)
_parser = JsonOutputParser(pydantic_object=IssueBundle)
_prompt = ChatPromptTemplate.from_messages([
    ("system", _load_prompt("issue_extraction")),
    ("human", "{question}\n\nJurisdiction: {state}\n\nFacts:\n{clause_text}"),
])
_chain = _prompt | _model | _parser


async def extract_issue(question: str, state: str, clause_text: str = "") -> IssueBundle:
    return await _chain.ainvoke({
        "question": question,
        "state": state,
        "clause_text": clause_text or "None provided.",
    })


def _load_prompt(name: str) -> str:
    path = Path(__file__).parent.parent / "prompts" / f"{name}.txt"
    return path.read_text(encoding="utf-8")
```

The public surface is `extract_issue`. Everything else is private.
The same pattern applies to `relevance_reducer.py` and `brief_writer.py`.

---

## Prompts

Prompts live in `.txt` files, not inline strings.

```
prompts/issue_extraction.txt
prompts/relevance_reduction.txt
prompts/brief_writing.txt
```

This keeps prompts editable and diffable without touching Python files.
Each prompt file contains the system prompt for its chain stage.
Load them once at module level with `_load_prompt()`.

Prompt files are not code — they do not follow the same comment rules.
Annotate them with plain-English notes at the top if the instructions
need context for a future editor.

---

## Tools

Each tool file wraps one MCP endpoint. The tool calls the MCP service over HTTP
and returns a typed result. No logic beyond the HTTP call and error handling.

```python
# tools/case_tool.py
#
# Fetches case law candidates from the MCP service.
# Called during Stage B of the orchestration chain.

import httpx
from models.internal import IssueBundle, RawCase
from exceptions import MCPError
from config import settings


async def fetch_cases(issue_bundle: IssueBundle, state: str) -> list[RawCase]:
    payload = {
        "query": issue_bundle.case_query,
        "state": state,
        "mode": "semantic",
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.mcp_base_url}/cases/search",
                json=payload,
                timeout=15.0,
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        raise MCPError("MCP case search timed out")
    except httpx.HTTPStatusError as e:
        raise MCPError(f"MCP returned {e.response.status_code} for case search")

    return response.json()["results"]
```

---

## Models

Three files with distinct roles.

```python
# models/internal.py
#
# Pydantic models shared between chain stages.
# These shapes never leave the Backend — they are not API response shapes.

from pydantic import BaseModel


class IssueBundle(BaseModel):
    issue_label: str
    topic_tags: list[str]
    case_query: str
    bill_query: str
    fact_sensitive_points: list[str]
    need_bills: bool


class RawCase(BaseModel):
    case_name: str
    court: str
    date: str
    citation: str | None
    snippet: str
    url: str
    raw_score: float
```

```python
# models/responses.py
#
# Pydantic models for outbound API responses returned to the Frontend.

from pydantic import BaseModel
from typing import Literal, Optional


class Authority(BaseModel):
    kind: Literal["case", "bill"]
    title: str
    citation: Optional[str]
    court: Optional[str]
    date: str
    url: str
    why_pertinent: str
    key_point: str


class BriefResponse(BaseModel):
    issue_summary: str
    jurisdiction_used: str
    state_was_inferred: bool
    pertinent_authorities: list[Authority]
    fact_sensitive_considerations: list[str]
    coverage_note: str
```

---

## Error Handling

Define errors in `exceptions.py`. Raise in tools and chains. Catch in routers.

```python
# exceptions.py
#
# Custom exceptions for LLM and MCP service failures.

class LLMError(Exception):
    pass

class MCPError(Exception):
    pass
```

Never swallow exceptions silently:

```python
# BAD
try:
    result = await _chain.ainvoke(inputs)
except Exception:
    return {}

# GOOD
try:
    result = await _chain.ainvoke(inputs)
except Exception as e:
    raise LLMError(f"Issue extraction failed: {e}") from e
```

---

## Naming

| Thing | Convention | Example |
|---|---|---|
| Files | `snake_case` | `issue_extractor.py` |
| Public functions | `snake_case` | `extract_issue()` |
| Private helpers | `_snake_case` | `_load_prompt()` |
| Module-level constants | `_SCREAMING` or `_snake` | `_chain`, `_BASE_URL` |
| Classes | `PascalCase` | `IssueBundle` |

---

## Function Length

If a function exceeds ~20 lines, ask whether it has a second responsibility.
If it does, extract it. Never split a function into artificial pieces just to
hit a line count — a complex but singular transformation can stay together.