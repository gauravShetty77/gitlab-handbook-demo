import time
import logging
import functools

logger = logging.getLogger(__name__)

_RATE_LIMIT_KEYWORDS = ("429", "quota", "rate", "resource_exhausted", "too many requests")

MAX_RETRIES = 3
BASE_DELAY = 10


def is_rate_limit_error(exc: Exception) -> bool:
    """Check whether an exception looks like a rate-limit / quota error."""
    msg = str(exc).lower()
    return any(kw in msg for kw in _RATE_LIMIT_KEYWORDS)


def retry_on_rate_limit(fn=None, *, max_retries: int = MAX_RETRIES, base_delay: float = BASE_DELAY):
    """
    Decorator that retries a function on Gemini rate-limit errors.

    Uses exponential backoff:  base_delay * 2^attempt  (10 → 20 → 40 → 80 → 160s)
    Non-rate-limit exceptions are re-raised immediately.

    Can be used as:
        @retry_on_rate_limit
        def my_func(): ...

        @retry_on_rate_limit(max_retries=5, base_delay=15)
        def my_func(): ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    if not is_rate_limit_error(exc):
                        raise  # not a rate-limit error — fail fast
                    last_exc = exc
                    if attempt < max_retries - 1:
                        wait = base_delay * (2 ** attempt)
                        logger.warning(
                            "Rate-limited (attempt %d/%d). Retrying in %ds… [%s]",
                            attempt + 1, max_retries, wait, func.__name__,
                        )
                        time.sleep(wait)
            logger.error("Rate-limit retries exhausted for %s: %s", func.__name__, last_exc)
            raise last_exc
        return wrapper

    # Allow bare @retry_on_rate_limit (no parentheses)
    if fn is not None:
        return decorator(fn)
    return decorator
