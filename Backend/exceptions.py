# exceptions.py
#
# Custom exceptions for LLM and MCP service failures.


class LLMError(Exception):
    """Raised when LangChain or Claude API calls fail."""
    pass


class MCPError(Exception):
    """Raised when MCP service or tool calls fail."""
    pass
