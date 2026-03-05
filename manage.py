#!/usr/bin/env python
import os
import sys
import logging
from pathlib import Path

def _configure_logging():
    log_level = os.getenv("DJANGO_LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s [%(process)d] %(levelname)s %(module)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]

def _ensure_settings_module():
    if "DJANGO_SETTINGS_MODULE" not in os.environ:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def _handle_missing_dependencies():
    try:
        import django
    except ImportError as exc:
        message = (
            "Django is required to run this project. "
            "Install it with 'pip install -r requirements.txt'."
        )
        raise RuntimeError(message) from exc

def main():
    _configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Django management script")
    _handle_missing_dependencies()
    _ensure_settings_module()
    try:
        from django.core.management import execute_from_command_line
    except Exception as exc:
        logger.exception("Failed to import Django's command line utilities")
        raise RuntimeError("Django installation is corrupted") from exc
    args = sys.argv[1:]
    if not args:
        logger.warning("No command supplied; defaulting to 'runserver'")
        args = ["runserver", "0.0.0.0:8000"]
    try:
        execute_from_command_line([sys.argv[0]] + args)
    except Exception as exc:
        logger.exception("Command execution failed")
        sys.exit(1)

if __name__ == "__main__":
    main()