from langchain_core.callbacks import BaseCallbackHandler
from typing import Any, Dict, Optional
from langchain_core.outputs import LLMResult


class TokenCountingCallback(BaseCallbackHandler):
    """
    LangChain callback handler for tracking token usage during LLM calls.
    Accumulates token counts across all LLM invocations in a chain.
    """
    
    def __init__(self):
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.successful_requests = 0
        
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM completes. Extract token usage from response."""
        if response.llm_output and "usage" in response.llm_output:
            usage = response.llm_output["usage"]
            self.total_tokens += usage.get("total_tokens", 0)
            self.prompt_tokens += usage.get("prompt_tokens", 0)
            self.completion_tokens += usage.get("completion_tokens", 0)
            self.successful_requests += 1
    
    def get_usage(self) -> Dict[str, int]:
        """Return current token usage statistics."""
        return {
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "requests": self.successful_requests
        }
    
    def reset(self) -> None:
        """Reset all counters."""
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.successful_requests = 0
