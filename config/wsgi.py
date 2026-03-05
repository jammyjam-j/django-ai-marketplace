import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    application = get_wsgi_application()
except Exception as exc:
    raise RuntimeError(f'WSGI application failed to initialize: {exc}') from exc