# routers/analyze.py
#
# Main analysis endpoint for legal research brief generation.
# Orchestrates the full chain: issue extraction → retrieval → reduction → brief.

from fastapi import APIRouter, HTTPException, Request
import asyncio
from models.schemas import AnalyzeRequest, BriefResponse
from chains.issue_extractor import extract_issue
from chains.relevance_reducer import reduce_to_pertinent
from chains.brief_writer import write_brief
from tools.case_tool import fetch_cases
from tools.bill_tool import fetch_bills
from tools.geo_tool import infer_state_from_ip
from exceptions import LLMError, MCPError

router = APIRouter()


@router.post("/api/analyze", response_model=BriefResponse)
async def analyze_legal_question(request: AnalyzeRequest, req: Request) -> BriefResponse:
    """
    Analyze a legal question and return a structured research brief.
    
    This endpoint orchestrates the full LangChain workflow:
    1. IP-based state inference (if no state_override)
    2. Issue extraction via LLM
    3. Parallel case and bill searches via MCP
    4. Relevance reduction via LLM
    5. Final brief writing via LLM
    
    Args:
        request: AnalyzeRequest with question, optional clause_text, state_override, search_mode
        req: FastAPI Request object for extracting IP
        
    Returns:
        BriefResponse with structured legal research brief
        
    Raises:
        HTTPException: 502 if LLM or MCP services fail
    """
    try:
        # Stage 0: Determine jurisdiction
        state, state_was_inferred = await _determine_jurisdiction(request, req)
        
        # Stage A: Issue Extraction
        issue_bundle = await extract_issue(
            request.question,
            state,
            request.clause_text or ""
        )
        
        # Stage B: Parallel Retrieval
        raw_cases, raw_bills = await _run_retrieval(
            issue_bundle,
            state,
            request.search_mode
        )
        
        # Stage C: Relevance Reduction
        pertinent_authorities = await reduce_to_pertinent(
            issue_bundle,
            raw_cases,
            raw_bills
        )
        
        # Stage D: Brief Writing
        return await write_brief(
            issue_bundle,
            pertinent_authorities,
            state,
            state_was_inferred
        )
        
    except LLMError as e:
        raise HTTPException(
            status_code=502,
            detail=f"LLM service error: {str(e)}"
        )
    except MCPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"MCP service error: {str(e)}"
        )


@router.get("/api/detect-state")
async def detect_state(req: Request):
    """
    Detect state from client IP address.
    
    This endpoint is used by the Frontend to pre-fill the jurisdiction selector
    based on the user's location inferred from their IP address.
    
    Returns:
        Dictionary with state_code field
    """
    try:
        ip = _extract_ip(req)
        state_code = await infer_state_from_ip(ip)
        return {"state_code": state_code}
    except MCPError:
        return {"state_code": "CA"}


async def _determine_jurisdiction(request: AnalyzeRequest, req: Request) -> tuple[str, bool]:
    """
    Determine the jurisdiction for legal research.
    
    Returns:
        Tuple of (state_code, was_inferred)
    """
    if request.state_override:
        return request.state_override, False
    
    # Infer from IP
    ip = _extract_ip(req)
    state = await infer_state_from_ip(ip)
    return state, True


def _extract_ip(req: Request) -> str:
    """
    Extract client IP from request headers.
    Checks x-forwarded-for first (for proxies/load balancers), then falls back to client.host.
    """
    forwarded = req.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    if req.client and req.client.host:
        return req.client.host
    
    return "8.8.8.8"


async def _run_retrieval(issue_bundle, state: str, search_mode: str) -> tuple[list, list]:
    """
    Run parallel retrieval of cases and bills.
    Bills are only fetched if issue_bundle indicates they're needed.
    
    Returns:
        Tuple of (raw_cases, raw_bills)
    """
    tasks = [fetch_cases(issue_bundle, state, search_mode)]
    
    if issue_bundle.need_bills:
        tasks.append(fetch_bills(issue_bundle, state))
    
    results = await asyncio.gather(*tasks)
    
    raw_cases = results[0][0]
    raw_bills = results[1][0] if len(results) > 1 else []
    
    return raw_cases, raw_bills
