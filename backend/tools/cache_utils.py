from functools import wraps
import logging

logger = logging.getLogger(__name__)

def with_cache(ttl_seconds: int = 3600):
    """
    A simple pass-through decorator since Redis caching is currently disabled.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator

