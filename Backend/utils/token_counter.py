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
        
        # Try modern format first (ChatAnthropic returns AIMessage with usage_metadata)
        if response.generations and len(response.generations) > 0:
            generation = response.generations[0]
            if hasattr(generation, 'message') and hasattr(generation.message, 'usage_metadata'):
                metadata = generation.message.usage_metadata
                # Anthropic uses input_tokens/output_tokens, need to map to standard names
                total = metadata.get("total_tokens", 0)
                prompt = metadata.get("input_tokens", 0)
                completion = metadata.get("output_tokens", 0)
                
                print(f"[TOKENS] Modern format extracted: total={total}, prompt={prompt}, completion={completion}")
                print(f"[TOKENS] Full usage_metadata: {metadata}")
                
                self.total_tokens += total
                self.prompt_tokens += prompt
                self.completion_tokens += completion
                self.successful_requests += 1
                return
        
        # Fallback to legacy format (llm_output.usage)
        if response.llm_output and "usage" in response.llm_output:
            usage = response.llm_output["usage"]
            
            # Anthropic provides input_tokens/output_tokens but not total_tokens
            # Calculate total if not provided
            input_tok = usage.get("input_tokens", 0)
            output_tok = usage.get("output_tokens", 0)
            total = usage.get("total_tokens", input_tok + output_tok)  # Calculate if missing
            
            prompt = usage.get("prompt_tokens", input_tok)  # Fallback to input_tokens
            completion = usage.get("completion_tokens", output_tok)  # Fallback to output_tokens
            
            print(f"[TOKENS] Legacy format extracted: total={total}, prompt={prompt}, completion={completion}")
            print(f"[TOKENS] Full llm_output.usage: {usage}")
            
            self.total_tokens += total
            self.prompt_tokens += prompt
            self.completion_tokens += completion
            self.successful_requests += 1
            return
        
        # No usage data found
        print(f"[TOKENS] No usage data found in response")
        print(f"[TOKENS] Response structure: {type(response)}")
        print(f"[TOKENS] Response.llm_output: {getattr(response, 'llm_output', 'None')}")
        print(f"[TOKENS] Response.generations: {getattr(response, 'generations', 'None')}")
    
    def get_usage(self) -> Dict[str, int]:
        """Return current token usage statistics."""
        
        usage = {
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "requests": self.successful_requests
        }
        
        print(f"[TOKENS] Cumulative usage: {usage}")
        return usage
    
    def reset(self) -> None:
        """Reset all counters."""
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.successful_requests = 0
