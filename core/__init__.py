import os
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

try:
    from dotenv import load_dotenv
except ImportError as exc:
    raise RuntimeError("python-dotenv is required for environment loading") from exc


class EnvironmentError(RuntimeError):
    pass


class ValidationError(EnvironmentError):
    pass


def _ensure_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Environment file not found at {path}")


def load_environment(dotenv_path: Optional[Path] = None, required_keys: Iterable[str] | None = None) -> Dict[str, str]:
    if dotenv_path is None:
        dotenv_path = Path(__file__).parent.parent / ".env"
    _ensure_file(dotenv_path)
    load_dotenv(dotenv_path=dotenv_path, override=True)
    env_vars = dict(os.environ)
    if required_keys:
        missing = [key for key in required_keys if key not in env_vars]
        if missing:
            raise ValidationError(f"Missing required environment variables: {', '.join(missing)}")
    return env_vars


def cast_value(value: str, caster: Callable[[str], Any]) -> Any:
    try:
        return caster(value)
    except Exception as exc:
        raise EnvironmentError(f"Failed to cast value '{value}'") from exc


def get_env_var(name: str, default: Optional[Any] = None, caster: Callable[[str], Any] | None = None) -> Any:
    raw_value = os.getenv(name)
    if raw_value is None:
        if default is not None:
            return default
        raise EnvironmentError(f"Environment variable '{name}' is missing")
    if caster:
        return cast_value(raw_value, caster)
    return raw_value


def setup_logging(level: int = logging.INFO) -> None:
    logger = logging.getLogger()
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)


def validate_settings(settings: Dict[str, Any], schema: Dict[str, Callable[[Any], bool]]) -> None:
    errors: List[str] = []
    for key, validator in schema.items():
        value = settings.get(key)
        if value is None or not validator(value):
            errors.append(f"Invalid setting for {key}")
    if errors:
        raise ValidationError("; ".join(errors))


def load_settings() -> Dict[str, Any]:
    required = ["DEBUG", "SECRET_KEY", "DATABASE_URL"]
    env = load_environment(required_keys=required)
    settings: Dict[str, Any] = {
        "DEBUG": get_env_var("DEBUG", caster=lambda v: v.lower() in ("1", "true")),
        "SECRET_KEY": get_env_var("SECRET_KEY"),
        "DATABASE_URL": get_env_var("DATABASE_URL"),
    }
    schema = {
        "DEBUG": lambda v: isinstance(v, bool),
        "SECRET_KEY": lambda v: isinstance(v, str) and len(v) >= 32,
        "DATABASE_URL": lambda v: isinstance(v, str) and v.startswith(("postgres://", "sqlite://")),
    }
    validate_settings(settings, schema)
    return settings


if __name__ == "__main__":
    setup_logging()
    try:
        cfg = load_settings()
        logging.info(f"Configuration loaded successfully: {cfg}")
    except Exception as exc:
        logging.exception("Failed to load configuration")
        raise