# models/schemas.py
#
# Pydantic models for Backend API request and response schemas.

from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class AnalyzeRequest(BaseModel):
    """
    Request schema for POST /api/analyze endpoint.
    
    The Frontend sends this to request a legal research brief.
    """
    question: str = Field(
        ...,
        description="Plain-English legal question from the user",
        examples=["Can a text message form a binding contract for website services?"]
    )
    clause_text: Optional[str] = Field(
        default=None,
        description="Optional contract clause text for context",
        examples=["Client agrees to pay $5000 for website design services"]
    )
    state_override: Optional[str] = Field(
        default=None,
        description="User-selected state code (e.g., 'CA', 'NY') - overrides IP-based inference",
        examples=["CA", "NY", "TX"]
    )
    search_mode: Literal["semantic", "keyword"] = Field(
        default="semantic",
        description="Case search mode: 'semantic' for meaning-based, 'keyword' for exact terms"
    )


class Authority(BaseModel):
    """
    Individual legal authority (case or bill) in the brief response.
    """
    kind: Literal["case", "bill"] = Field(
        ...,
        description="Type of authority: 'case' for case law, 'bill' for legislation"
    )
    title: str = Field(
        ...,
        description="Case name or bill title",
        examples=["Smith v. Jones", "Electronic Signatures Act"]
    )
    citation: Optional[str] = Field(
        default=None,
        description="Legal citation (cases only)",
        examples=["123 Cal. 4th 567"]
    )
    court: Optional[str] = Field(
        default=None,
        description="Court name (cases only)",
        examples=["Supreme Court of California"]
    )
    date: str = Field(
        ...,
        description="Decision date or latest action date",
        examples=["2023-05-15"]
    )
    url: str = Field(
        ...,
        description="URL to the full authority text"
    )
    why_pertinent: str = Field(
        ...,
        description="Explanation of how this authority relates to the user's specific facts",
        examples=["Addresses whether text messages can form valid contract acceptance"]
    )
    key_point: str = Field(
        ...,
        description="The holding or provision that matters for this issue",
        examples=["Text messages can constitute acceptance if terms are sufficiently definite"]
    )
    status: Optional[str] = Field(
        default=None,
        description="Precedential status for cases: Published, Unpublished, etc."
    )
    judge: Optional[str] = Field(
        default=None,
        description="Authoring judge for cases"
    )
    posture: Optional[str] = Field(
        default=None,
        description="Procedural posture for cases: Affirmed, Reversed, etc."
    )
    cite_count: Optional[int] = Field(
        default=None,
        description="Number of citations (cases only)"
    )
    sponsors: Optional[List[dict]] = Field(
        default=None,
        description="Bill sponsors with name and party"
    )


class BriefResponse(BaseModel):
    """
    Response schema for POST /api/analyze endpoint.
    
    The Backend returns this structured brief to the Frontend.
    """
    issue_summary: str = Field(
        ...,
        description="Simple-language framing of the detected legal issue",
        examples=["Whether a text message exchange can form an enforceable contract for website services"]
    )
    analysis_summary: str = Field(
        ...,
        description="1-2 paragraph analysis integrating case law and providing a framework for answering the legal question",
        examples=["Under contract law, text messages can form binding agreements if they contain all essential terms..."]
    )
    jurisdiction_used: str = Field(
        ...,
        description="State code used for the research (e.g., 'CA', 'NY')",
        examples=["CA", "OR", "NY"]
    )
    state_was_inferred: bool = Field(
        ...,
        description="True if jurisdiction was inferred from IP, False if user-selected"
    )
    pertinent_authorities: List[Authority] = Field(
        default_factory=list,
        description="List of relevant legal authorities (cases and bills)"
    )
    fact_sensitive_considerations: List[str] = Field(
        default_factory=list,
        description="List of fact-dependent questions that could change the outcome",
        examples=[
            ["Was there clear acceptance of the offer?", 
             "Were the price and scope sufficiently definite?",
             "Did either party begin performance?"]
        ]
    )
    coverage_note: str = Field(
        ...,
        description="Explanation of what was searched, what was excluded, and any uncertainty",
        examples=["Searched California contract law; excluded federal cases; limited to contracts formed electronically"]
    )
