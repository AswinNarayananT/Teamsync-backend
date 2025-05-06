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
            return await self.close()

        self.group_name = f"workspace_{self.workspace_id}_user_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        data = await self.fetch_notifications(self.user.id, self.workspace_id)
        await self.send(json.dumps({
            'type': 'init',
            'notifications': data['notifications'],
            'unread_count': data['unread_count'],
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
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
        unread_count = qs.filter(is_read=False).count()
        return {
            'notifications': [
                {
                    'message': n.message,
                    'created_at': n.created_at.isoformat(),
                    'is_read': n.is_read,
                } for n in qs
            ],
            'unread_count': unread_count,
        }
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'mark_read':
            await self.mark_all_as_read(self.user.id, self.workspace_id)

    @database_sync_to_async
    def mark_all_as_read(self, user_id, workspace_id):
        Notification.objects.filter(
            recipient_id=user_id,
            workspace_id=workspace_id,
            is_read=False
        ).update(is_read=True)