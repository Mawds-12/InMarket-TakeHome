# exceptions.py
#
# Custom exceptions for external service failures.
# Raised in client modules; caught in tools to return clean error messages.


class CourtListenerError(Exception):
    """Raised when CourtListener API calls fail."""
    pass


class OpenStatesError(Exception):
    """Raised when Open States API calls fail."""
    pass


class IPInfoError(Exception):
    """Raised when IPinfo API calls fail."""
    pass
