"""
Rate limiting utilities for API endpoints.
"""

import os
from slowapi import Limiter
from slowapi.util import get_remote_address


# Global limiter instance
limiter = Limiter(key_func=get_remote_address)


def conditional_limiter(limit_string):
    """
    Apply rate limiting only if enabled in settings.
    
    This decorator conditionally applies rate limiting based on the
    RATE_LIMITING_ENABLED environment variable. This is useful for
    disabling rate limiting in test environments while keeping it
    enabled in production.
    
    Args:
        limit_string: Rate limit string (e.g., "20/minute")
        
    Returns:
        Decorator function that may or may not apply rate limiting
        
    Example:
        @router.post("/api/endpoint")
        @conditional_limiter("20/minute")
        async def my_endpoint():
            pass
    """
    def decorator(func):
        # Check environment variable directly (for test compatibility)
        rate_limiting_enabled = os.getenv("RATE_LIMITING_ENABLED", "true").lower() != "false"
        
        if not rate_limiting_enabled:
            # Return original function without rate limiting
            return func
        
        # Apply rate limiting
        return limiter.limit(limit_string)(func)
    
    return decorator

