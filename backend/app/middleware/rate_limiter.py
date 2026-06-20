"""
Rate limiting middleware using an in-memory sliding window algorithm.

Limits are applied per (user_id, endpoint) pair. Limits and windows
are configured via environment variables in Settings.
"""

import time
from collections import defaultdict, deque
from fastapi import HTTPException, status
from app.config import settings

class RateLimiter:
    """Thread-safe sliding window rate limiter backed by a deque per key."""
    def __init__(self):
        self.requests = defaultdict(deque)

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        Check whether a request is within the allowed rate limit.

        Args:
            key:            Unique identifier string (e.g. "user123:analyze").
            limit:          Maximum number of requests allowed in the window.
            window_seconds: Length of the sliding window in seconds.

        Returns:
            True if the request is allowed; False if the limit is exceeded.
        """
        now = time.time()
        cutoff = now - window_seconds
        
        dq = self.requests[key]
        while dq and dq[0] < cutoff:
            dq.popleft()
            
        if len(dq) >= limit:
            return False
            
        dq.append(now)
        return True

rate_limiter = RateLimiter()

def check_rate_limit(user_id: str, endpoint: str, settings_attr: str):
    """
    Enforce a rate limit for the given user and endpoint.

    Reads the limit value from settings using settings_attr as the
    attribute name. Derives the window duration from the attribute suffix
    (_rpm = 60 s, _rph = 3600 s).

    Raises:
        HTTPException 429: If the user has exceeded the allowed rate.
    """
    limit = getattr(settings, settings_attr, 10)
    
    if settings_attr.endswith("_rpm"):
        window_seconds = 60
    elif settings_attr.endswith("_rph"):
        window_seconds = 3600
    else:
        window_seconds = 60
        
    key = f"{user_id}:{endpoint}"
    
    if not rate_limiter.is_allowed(key, limit, window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before retrying."
        )
