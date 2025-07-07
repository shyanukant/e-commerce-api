"""
ASGI config for backend project.

- Exposes the ASGI callable as a module-level variable named `application`.
- Sets up ProtocolTypeRouter for both HTTP and WebSocket (Channels) support.
- WebSocket connections are routed to orders app consumers.
"""
import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from orders.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django_asgi_app = get_asgi_application()

# ProtocolTypeRouter allows handling both HTTP and WebSocket
application = ProtocolTypeRouter({
    'http': django_asgi_app,  # Standard Django HTTP
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)  # WebSocket routes for order status updates
    ),
})
