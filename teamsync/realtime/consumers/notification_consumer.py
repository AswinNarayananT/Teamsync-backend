# realtime/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from realtime.models import Notification

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.workspace_id = self.scope['url_route']['kwargs']['workspace_id']
        self.user = self.scope.get('user', AnonymousUser())

        if not self.user.is_authenticated:
            # Reject unauthenticated users
            return await self.close()

        # Build the exact group name that the view will broadcast to
        self.group_name = f"workspace_{self.workspace_id}_user_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Accept the WebSocket handshake
        await self.accept()

        # Fetch and send any existing notifications
        notifications = await self.fetch_notifications(self.user.id, self.workspace_id)
        await self.send(json.dumps({
            'type': 'init',
            'notifications': notifications,
        }))

    async def disconnect(self, close_code):
        # Clean up group membership
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        # Called by the group_send in your view
        await self.send(json.dumps({
            'type': 'new',
            'message': event['content']['message'],
        }))

    @database_sync_to_async
    def fetch_notifications(self, user_id, workspace_id):
        qs = Notification.objects.filter(
            recipient_id=user_id,
            workspace_id=workspace_id
        ).order_by('-created_at')
        return [
            {
                'message': n.message,
                'created_at': n.created_at.isoformat(),
                'is_read': n.is_read,
            }
            for n in qs
        ]
