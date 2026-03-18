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
from exceptions import LLMError


def _load_prompt(name: str) -> str:
    """Load prompt text from prompts directory."""
    path = Path(__file__).parent.parent / "prompts" / f"{name}.txt"
    return path.read_text(encoding="utf-8")


_model = ChatAnthropic(
    model=settings.anthropic_model,
    api_key=settings.anthropic_api_key,
)

_parser = JsonOutputParser(pydantic_object=IssueBundle)

_prompt = ChatPromptTemplate.from_messages([
    ("system", _load_prompt("issue_extraction")),
    ("human", "Question: {question}\n\nJurisdiction: {state}\n\nFacts/Context:\n{clause_text}"),
])

_chain = _prompt | _model | _parser


async def extract_issue(question: str, state: str, clause_text: str = "", callbacks=None) -> IssueBundle:
    """
    Extract structured issue information from a legal question.
    
    Args:
        question: User's plain-English legal question
        state: Jurisdiction code (e.g., "CA", "NY")
        clause_text: Optional contract clause or factual context
        callbacks: Optional LangChain callbacks for tracking token usage
        
    Returns:
        IssueBundle with search queries and metadata
        
    Raises:
        LLMError: If issue extraction fails
    """
    try:
        config = {"callbacks": callbacks} if callbacks else {}
        result = await _chain.ainvoke({
            "question": question,
            "state": state,
            "clause_text": clause_text or "None provided.",
        }, config=config)
        
        return IssueBundle(**result)
        
    except Exception as e:
        raise LLMError(f"Issue extraction failed: {str(e)}") from e
