# chains/relevance_reducer.py
#
# Stage C of the orchestration chain.
# Filters raw search results to only pertinent authorities.

from pathlib import Path
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from models.internal import IssueBundle, RawCase, RawBill
from models.schemas import Authority
from config import settings
from exceptions import LLMError


def _load_prompt(name: str) -> str:
    """Load prompt text from prompts directory."""
    path = Path(__file__).parent.parent / "prompts" / f"{name}.txt"
    return path.read_text(encoding="utf-8")


_model = ChatAnthropic(
    model=settings.anthropic_model,
    api_key=settings.anthropic_api_key,
)

_parser = JsonOutputParser()

_prompt = ChatPromptTemplate.from_messages([
    ("system", _load_prompt("relevance_reduction")),
    ("human", "IssueBundle:\n{issue_bundle}\n\nRaw Cases:\n{raw_cases}\n\nRaw Bills:\n{raw_bills}"),
])

_chain = _prompt | _model | _parser


async def reduce_to_pertinent(
    issue_bundle: IssueBundle,
    raw_cases: list[RawCase],
    raw_bills: list[RawBill],
    callbacks=None
) -> list[Authority]:
    """
    Filter raw search results to only pertinent authorities.
    
    Args:
        issue_bundle: Issue extraction output
        raw_cases: Raw case results from MCP
        raw_bills: Raw bill results from MCP
        callbacks: Optional LangChain callbacks for tracking token usage
        
    Returns:
        List of pertinent Authority objects with why_pertinent and key_point populated
        
    Raises:
        LLMError: If relevance reduction fails
    """
    try:
        config = {"callbacks": callbacks} if callbacks else {}
        result = await _chain.ainvoke({
            "issue_bundle": json.dumps(issue_bundle.model_dump(), indent=2),
            "raw_cases": json.dumps([case.model_dump() for case in raw_cases], indent=2),
            "raw_bills": json.dumps([bill.model_dump() for bill in raw_bills], indent=2),
        }, config=config)
        
        return [Authority(**auth) for auth in result]
        
    except Exception as e:
        raise LLMError(f"Relevance reduction failed: {str(e)}") from e
