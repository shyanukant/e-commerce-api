"""
WebSocket URL routing for the orders app (Channels).
Maps WebSocket connections to the OrderStatusConsumer.
"""
from django.urls import re_path
from . import consumers

# WebSocket endpoint for order status updates
websocket_urlpatterns = [
    re_path(r'ws/orders/$', consumers.OrderStatusConsumer.as_asgi()),
] 