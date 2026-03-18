# chains/brief_writer.py
#
# Stage D of the orchestration chain.
# Writes the final structured brief from pertinent authorities.

from pathlib import Path
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from models.internal import IssueBundle
from models.schemas import Authority, BriefResponse
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

_parser = JsonOutputParser(pydantic_object=BriefResponse)

_prompt = ChatPromptTemplate.from_messages([
    ("system", _load_prompt("brief_writing")),
    ("human", "IssueBundle:\n{issue_bundle}\n\nPertinent Authorities:\n{pertinent_authorities}\n\nJurisdiction: {state}\nState was inferred: {state_was_inferred}"),
])

_chain = _prompt | _model | _parser


async def write_brief(
    issue_bundle: IssueBundle,
    pertinent_authorities: list[Authority],
    state: str,
    state_was_inferred: bool
) -> BriefResponse:
    """
    Write the final structured brief.
    
    Args:
        issue_bundle: Issue extraction output
        pertinent_authorities: Filtered authorities from relevance reduction
        state: Jurisdiction code used
        state_was_inferred: Whether state was inferred from IP
        
    Returns:
        Complete BriefResponse with all fields populated
        
    Raises:
        LLMError: If brief writing fails
    """
    try:
        result = await _chain.ainvoke({
            "issue_bundle": json.dumps(issue_bundle.model_dump(), indent=2),
            "pertinent_authorities": json.dumps([auth.model_dump() for auth in pertinent_authorities], indent=2),
            "state": state,
            "state_was_inferred": str(state_was_inferred),
        })
        
        return BriefResponse(**result)
        
    except Exception as e:
        raise LLMError(f"Brief writing failed: {str(e)}") from e
