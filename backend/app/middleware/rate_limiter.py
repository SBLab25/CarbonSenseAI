import time
from collections import defaultdict, deque
from fastapi import HTTPException, status
from app.config import settings

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(deque)

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
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
