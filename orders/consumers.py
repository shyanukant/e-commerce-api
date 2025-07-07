"""
WebSocket consumer for real-time order status updates using Django Channels.
Handles user authentication, group management, and event broadcasting.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Order

class OrderStatusConsumer(AsyncWebsocketConsumer):
    """
    Handles real-time order status updates for users via WebSocket.
    Receives 'order_status_update' events from the channel layer and sends them to the client.
    """
    async def connect(self):
        self.user = self.scope["user"]
        # Only allow authenticated users to connect
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
        self.room_name = f"user_{self.user.id}_orders"
        self.room_group_name = f"orders_{self.user.id}"
        # Join the user's order group for status updates
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the user's order group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Handle messages from the client (e.g., subscribe to a specific order)
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'message')
        if message_type == 'subscribe_order':
            order_id = text_data_json.get('order_id')
            if order_id:
                # Join a group for a specific order (optional granularity)
                await self.channel_layer.group_add(
                    f"order_{order_id}",
                    self.channel_name
                )
                await self.send(text_data=json.dumps({
                    'type': 'subscription_confirmed',
                    'order_id': order_id
                }))

    async def order_status_update(self, event):
        # Send order status update to WebSocket client
        await self.send(text_data=json.dumps({
            'type': 'order_status_update',
            'order_id': event['order_id'],
            'status': event['status'],
            'message': event.get('message', '')
        }))

    @database_sync_to_async
    def get_user_orders(self):
        """Return a list of the user's orders and their statuses."""
        return list(Order.objects.filter(user=self.user).values('id', 'status')) 