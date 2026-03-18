# routers/dev.py
#
# Development and testing endpoints.
# These endpoints test individual stages of the pipeline in isolation.

from fastapi import APIRouter
from models.schemas import AnalyzeRequest, BriefResponse
from models.internal import IssueBundle
from chains.issue_extractor import extract_issue
from chains.relevance_reducer import reduce_to_pertinent
from chains.brief_writer import write_brief
from tools.case_tool import fetch_cases
from tools.bill_tool import fetch_bills
from tools.geo_tool import infer_state_from_ip

router = APIRouter()


@router.post("/api/dev/test-issue-extraction")
async def test_issue_extraction(question: str, state: str = "CA", clause_text: str = "") -> IssueBundle:
    """
    Test Stage A: Issue Extraction
    
    Extracts structured IssueBundle from a legal question.
    """
    return await extract_issue(question, state, clause_text)


@router.post("/api/dev/test-case-search")
async def test_case_search(query: str, state: str = "CA", mode: str = "semantic"):
    """
    Test MCP case search tool.
    
    Calls CourtListener via MCP to fetch raw case results.
    """
    from models.internal import IssueBundle
    
    # Create minimal IssueBundle for testing
    issue_bundle = IssueBundle(
        issue_label="test",
        topic_tags=["test"],
        case_query=query,
        bill_query="",
        fact_sensitive_points=["test"],
        need_bills=False
    )
    
    return await fetch_cases(issue_bundle, state, mode)


@router.post("/api/dev/test-bill-search")
async def test_bill_search(query: str, state: str = "CA"):
    """
    Test MCP bill search tool.
    
    Calls Open States via MCP to fetch raw bill results.
    """
    from models.internal import IssueBundle
    
    # Create minimal IssueBundle for testing
    issue_bundle = IssueBundle(
        issue_label="test",
        topic_tags=["test"],
        case_query="",
        bill_query=query,
        fact_sensitive_points=["test"],
        need_bills=True
    )
    
    return await fetch_bills(issue_bundle, state)


@router.post("/api/dev/test-geo-lookup")
async def test_geo_lookup(ip: str = "8.8.8.8"):
    """
    Test MCP IP geolocation tool.
    
    Calls IPinfo via MCP to infer state from IP.
    """
    return await infer_state_from_ip(ip)


@router.post("/api/dev/test-full-pipeline")
async def test_full_pipeline(question: str, state: str = "CA", search_mode: str = "semantic") -> BriefResponse:
    """
    Test the complete pipeline with a simple question.
    
    Useful for debugging the full flow without the Frontend.
    """
    # Stage A: Extract issue
    issue_bundle = await extract_issue(question, state, "")
    
    # Stage B: Fetch raw results
    raw_cases = await fetch_cases(issue_bundle, state, search_mode)
    raw_bills = await fetch_bills(issue_bundle, state) if issue_bundle.need_bills else []
    
    # Stage C: Reduce to pertinent
    pertinent_authorities = await reduce_to_pertinent(issue_bundle, raw_cases, raw_bills)
    
    # Stage D: Write brief
    return await write_brief(issue_bundle, pertinent_authorities, state, False)
