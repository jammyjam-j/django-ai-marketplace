import os
from django.core.asgi import get_asgi_application
from django.urls import path, re_path
from django.http import HttpResponseNotFound, HttpRequest
from typing import Callable, Awaitable

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

async def custom_404(request: HttpRequest) -> HttpResponseNotFound:
    return HttpResponseNotFound("Page not found")

urlpatterns = [
    re_path(r'^.*$', custom_404),
]

class ASGIHandler:
    def __init__(self, app: Callable[..., Awaitable] = None):
        self.app = app or django_asgi_app
        self._validate_application()

    def _validate_application(self) -> None:
        if not callable(self.app):
            raise TypeError("ASGI application must be callable")
        required_attrs = ('__call__',)
        for attr in required_attrs:
            if not hasattr(self.app, attr):
                raise AttributeError(f"Missing required attribute {attr} on ASGI app")

    async def __call__(self, scope: dict, receive: Callable[[dict], Awaitable], send: Callable[[dict], Awaitable]) -> None:
        await self.app(scope, receive, send)

application = ASGIHandler()
asgi_application = application
django_asgi_app = get_asgi_application()  # reassign for consistency

async def get_response_for_path(path: str) -> Callable[..., Awaitable]:
    if path == '/admin/':
        return django_asgi_app
    return custom_404

async def handle_scope(scope: dict, receive: Callable[[dict], Awaitable], send: Callable[[dict], Awaitable]) -> None:
    if scope.get('type') != 'http':
        await application(scope, receive, send)
        return
    path = scope.get('path', '')
    handler = await get_response_for_path(path)
    await handler(scope, receive, send)

application = ASGIHandler(handle_scope)