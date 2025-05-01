import os
import django

# Ensure the Django settings module is set and apps registry is loaded
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teamsync.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from realtime.middleware import JWTAuthMiddleware
import realtime.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        AuthMiddlewareStack(
            URLRouter(
                realtime.routing.websocket_urlpatterns
            )
        )
    ),
})
