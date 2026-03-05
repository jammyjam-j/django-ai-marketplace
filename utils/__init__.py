from .decorators import retry_on_exception
from .validators import validate_email, validate_price
import os
import json
import logging

logger = logging.getLogger(__name__)

def get_env_variable(name: str, default: str | None = None) -> str:
    value = os.getenv(name)
    if value is None:
        if default is not None:
            return default
        raise KeyError(f"Environment variable {name} not set")
    return value

def load_json_file(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        logger.error("JSON file not found: %s", path)
        raise e
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in file: %s", path)
        raise e

def ensure_list(value):
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]

def safe_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def log_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            logger.exception("Exception in %s", func.__name__)
            raise
    return wrapper

__all__ = [
    "get_env_variable",
    "load_json_file",
    "ensure_list",
    "safe_int",
    "log_exception",
    "retry_on_exception",
    "validate_email",
    "validate_price",
]