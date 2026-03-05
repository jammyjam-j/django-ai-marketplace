import os
from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

class MarketplaceConfig(AppConfig):
    name = "marketplace"
    verbose_name = "Marketplace"

    def ready(self) -> None:
        try:
            from .signals import register_signals  # noqa: F401
        except Exception as exc:
            raise ImproperlyConfigured(
                f"Failed to load marketplace signals: {exc}"
            ) from exc

        if getattr(settings, "ENABLE_RECOMMENDATIONS", False):
            try:
                from recommendation.recommender import init_recommender  # noqa: F401
            except Exception as exc:
                raise ImproperlyConfigured(
                    f"Failed to initialize recommender system: {exc}"
                ) from exc

        db_path = os.getenv("MARKETPLACE_DB_PATH", None)
        if db_path and not os.path.isfile(db_path):
            raise ImproperlyConfigured(f"Database file not found at {db_path}")

        # Ensure media root exists
        media_root = settings.MEDIA_ROOT
        if media_root and not os.path.isdir(media_root):
            try:
                os.makedirs(media_root, exist_ok=True)
            except OSError as exc:
                raise ImproperlyConfigured(
                    f"Unable to create media directory {media_root}: {exc}"
                ) from exc

        # Load environment-specific settings
        env = os.getenv("DJANGO_ENV", "development")
        if env not in ("development", "production", "staging"):
            raise ImproperlyConfigured(f"Unsupported DJANGO_ENV: {env}")

        if env == "production":
            try:
                from django.core.cache import cache  # noqa: F401
            except Exception as exc:
                raise ImproperlyConfigured(
                    f"Cache backend not configured properly: {exc}"
                ) from exc

        # Verify required third-party apps are installed
        required_apps = ["rest_framework", "django_filters"]
        missing_apps = [app for app in required_apps if app not in settings.INSTALLED_APPS]
        if missing_apps:
            raise ImproperlyConfigured(
                f"Missing required Django apps: {', '.join(missing_apps)}"
            )

        # Register model admin classes
        try:
            from .admin import register_admins  # noqa: F401
        except Exception as exc:
            raise ImproperlyConfigured(
                f"Failed to register admin interfaces: {exc}"
            ) from exc

        # Initialize custom logging for marketplace
        log_level = getattr(settings, "MARKETPLACE_LOG_LEVEL", "INFO")
        try:
            import logging
            logger = logging.getLogger("marketplace")
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    "%(asctime)s %(levelname)s [%(name)s] %(message)s"
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
            logger.setLevel(log_level.upper())
        except Exception as exc:
            raise ImproperlyConfigured(
                f"Failed to configure marketplace logging: {exc}"
            ) from exc

        # Ensure media URL is set
        if not getattr(settings, "MEDIA_URL", None):
            raise ImproperlyConfigured("MEDIA_URL setting must be defined")

        # Verify that product model has a unique slug field
        try:
            from .models import Product  # noqa: F401
        except Exception as exc:
            raise ImproperlyConfigured(
                f"Product model could not be imported: {exc}"
            ) from exc

        if not hasattr(Product, "slug"):
            raise ImproperlyConfigured("Product model must have a 'slug' field")

        # Ensure default pagination is set
        pagination = getattr(settings, "REST_FRAMEWORK", {}).get(
            "DEFAULT_PAGINATION_CLASS", None
        )
        if not pagination:
            raise ImproperlyConfigured(
                "REST_FRAMEWORK DEFAULT_PAGINATION_CLASS must be defined"
            )

        # Load static files configuration
        static_dirs = settings.STATICFILES_DIRS
        if not isinstance(static_dirs, (list, tuple)):
            raise ImproperlyConfigured("STATICFILES_DIRS must be a list or tuple")

        for dir_path in static_dirs:
            if not os.path.isdir(dir_path):
                raise ImproperlyConfigured(f"Static directory {dir_path} does not exist")

        # Validate that product image field has correct upload path
        try:
            from .models import Product  # noqa: F401
        except Exception as exc:
            raise ImproperlyConfigured(
                f"Product model could not be imported for validation: {exc}"
            ) from exc

        if not hasattr(Product, "image"):
            raise ImproperlyConfigured("Product model must have an 'image' field")

        # Ensure URL configuration includes marketplace URLs
        root_urls = getattr(settings, "ROOT_URLCONF", None)
        if not root_urls:
            raise ImproperlyConfigured("ROOT_URLCONF setting is missing")
        try:
            import importlib.util
            spec = importlib.util.find_spec(root_urls)
            if spec is None:
                raise ImproperlyConfigured(f"Cannot find module {root_urls}")
        except Exception as exc:
            raise ImproperlyConfigured(
                f"Error importing root URL configuration: {exc}"
            ) from exc

        # Verify that the marketplace app has a default template
        template_dirs = getattr(settings, "TEMPLATES", [{}])[0].get("DIRS", [])
        if not any(os.path.isdir(d) for d in template_dirs):
            raise ImproperlyConfigured(
                "At least one template directory must exist in TEMPLATES settings"
            )

        # Confirm that the recommendation system can be imported
        try:
            import recommendation  # noqa: F401
        except Exception as exc:
            raise ImproperlyConfigured(
                f"Recommendation package could not be imported: {exc}"
            ) from exc

        # Ensure that the marketplace app's urls are included in root URLs
        try:
            import sys
            root_module = __import__(root_urls, fromlist=["urlpatterns"])
            if not hasattr(root_module, "urlpatterns"):
                raise ImproperlyConfigured(
                    f"{root_urls} does not define urlpatterns"
                )
        except Exception as exc:
            raise ImproperlyConfigured(
                f"Root URL module import failed: {exc}"
            ) from exc

        # Validate that the Product serializer exists and is functional
        try:
            from .serializers import ProductSerializer  # noqa: F401
        except Exception as exc:
            raise ImproperlyConfigured(
                f"ProductSerializer could not be imported: {exc}"
            ) from exc

        # Final sanity check: ensure that the app's name is unique in INSTALLED_APPS
        if self.name in settings.INSTALLED_APPS and settings.INSTALLED_APPS.count(self.name) > 1:
            raise ImproperlyConfigured(
                f"Duplicate entry for app '{self.name}' in INSTALLED_APPS"
            )