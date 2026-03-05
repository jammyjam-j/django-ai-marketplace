import time
from functools import wraps
from typing import Any, Callable, Dict, Tuple

_cache_store: Dict[Tuple[Any, ...], Tuple[Any, float]] = {}


def cache(ttl_seconds: int) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = (func.__module__, func.__qualname__, args, tuple(sorted(kwargs.items())))
            cached = _cache_store.get(key)
            if cached is not None:
                result, expire_at = cached
                if time.time() < expire_at:
                    return result
            result = func(*args, **kwargs)
            _cache_store[key] = (result, time.time() + ttl_seconds)
            return result

        return wrapper

    return decorator


def require_authentication(view_func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request, "user") or request.user is None:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Authentication required.")
        if not getattr(request.user, "is_authenticated", False):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("User not authenticated.")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def log_execution(logger_name: str = __name__) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    import logging

    logger = logging.getLogger(logger_name)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.debug(f"Entering {func.__qualname__} with args={args}, kwargs={kwargs}")
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                logger.debug(f"Exiting {func.__qualname__} took {duration:.4f}s")

        return wrapper

    return decorator

def timed_cache(ttl_seconds: int) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        cache_dict: Dict[Tuple[Any, ...], Tuple[Any, float]] = {}

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = (func.__module__, func.__qualname__, args, tuple(sorted(kwargs.items())))
            entry = cache_dict.get(key)
            if entry is not None:
                result, expire_at = entry
                if time.time() < expire_at:
                    return result
            result = func(*args, **kwargs)
            cache_dict[key] = (result, time.time() + ttl_seconds)
            return result

        return wrapper

    return decorator

def throttle(rate_limit: int) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Simple in-memory request throttling per user key. rate_limit specifies max calls per minute.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        usage_store: Dict[Any, Tuple[int, float]] = {}

        @wraps(func)
        def wrapper(request, *args, **kwargs):
            user_key = getattr(request, "user", None) or request.META.get("REMOTE_ADDR")
            count, window_start = usage_store.get(user_key, (0, time.time()))
            now = time.time()
            if now - window_start > 60:
                count, window_start = 0, now
            if count >= rate_limit:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Rate limit exceeded.")
            usage_store[user_key] = (count + 1, window_start)
            return func(request, *args, **kwargs)

        return wrapper

    return decorator