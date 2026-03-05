import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def _get_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")

def _load_secret(name: str, required: bool = True) -> str:
    secret = os.getenv(name)
    if required and not secret:
        raise RuntimeError(f"Required environment variable '{name}' is missing.")
    return secret or ""

SECRET_KEY = _load_secret("DJANGO_SECRET_KEY", required=True)

DEBUG = _get_bool(os.getenv("DJANGO_DEBUG"), default=False)

ALLOWED_HOSTS_ENV = os.getenv("DJANGO_ALLOWED_HOSTS", "")
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(",")]
else:
    ALLOWED_HOSTS = ["localhost"]

DATABASE_URL = _load_secret("POSTGRES_DB_URL", required=False)
if not DATABASE_URL:
    raise RuntimeError("Database URL must be provided via POSTGRES_DB_URL environment variable.")

def _parse_database_url(url: str) -> dict:
    import dj_database_url
    return dj_database_url.parse(url, conn_max_age=600)

DATABASES = {"default": _parse_database_url(DATABASE_URL)}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TIME_ZONE_ENV = os.getenv("DJANGO_TIME_ZONE", "UTC")
if TIME_ZONE_ENV not in ("UTC", "America/New_York", "Europe/London"):
    raise ValueError(f"Unsupported time zone: {TIME_ZONE_ENV}")
TIME_ZONE = TIME_ZONE_ENV

LANGUAGE_CODE = os.getenv("DJANGO_LANGUAGE_CODE", "en-us")

STATIC_URL = "/static/"

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

LOGGING_LEVEL = os.getenv("DJANGO_LOGGING_LEVEL", "INFO").upper()
if LOGGING_LEVEL not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
    raise ValueError(f"Invalid logging level: {LOGGING_LEVEL}")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"verbose": {"format": "%(levelname)s %(asctime)s %(module)s %(message)s"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": LOGGING_LEVEL},
}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "marketplace",
    "recommendation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(TEMPLATES_DIR)],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.debug", "django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]},
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticatedOrReadOnly"],
}

if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

def get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)

def assert_configured() -> None:
    required_vars = ["DJANGO_SECRET_KEY", "POSTGRES_DB_URL"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

assert_configured()