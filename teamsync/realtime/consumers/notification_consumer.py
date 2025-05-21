import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from realtime.models import Notification
from workspace.models import WorkspaceMember 

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user', AnonymousUser())
        print("WS CONNECT: ", self.user)

        if not self.user.is_authenticated:
            print("WS: Unauthenticated user tried to connect.")
            await self.close()
            return

        # Fetch all workspace IDs the user belongs to
        self.workspace_ids = await self.get_user_workspace_ids(self.user.id)

        # Define group names for each workspace-user combination
        self.group_names = [
            f"workspace_{workspace_id}_user_{self.user.id}"
            for workspace_id in self.workspace_ids
        ]

        # Add this connection to all relevant groups
        for group_name in self.group_names:
            await self.channel_layer.group_add(group_name, self.channel_name)

        await self.accept()

        # Send initial notifications and unread count
        data = await self.fetch_all_workspace_notifications(self.user.id)
        await self.send(json.dumps({
            'type': 'init',
            'notifications': data['notifications'],
            'unread_count': data['unread_count'],
        }))

    async def disconnect(self, close_code):
        for group_name in getattr(self, 'group_names', []):
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get('type') == 'mark_read':
            await self.mark_all_as_read(self.user.id)

    async def send_notification(self, event):
        # Receive notification from the group and send to the WebSocket
        await self.send(json.dumps({
            'type': 'new',
            'message': event['content']['message'],
            'workspace': event['content'].get('workspace'),  # Optional field for frontend display
        }))

    @database_sync_to_async
    def get_user_workspace_ids(self, user_id):
        return list(
            WorkspaceMember.objects.filter(user_id=user_id)
            .values_list('workspace_id', flat=True)
        )

    @database_sync_to_async
    def fetch_all_workspace_notifications(self, user_id):
        qs = Notification.objects.filter(
            recipient_id=user_id
        ).select_related('workspace').order_by('-created_at')

        unread_count = qs.filter(is_read=False).count()

        return {
            'notifications': [
                {
                    'message': n.message,
                    'created_at': n.created_at.isoformat(),
                    'is_read': n.is_read,
                    'workspace': {
                        'id': n.workspace.id,
                        'name': n.workspace.name,
                    }
                } for n in qs
            ],
            'unread_count': unread_count,
        }

    @database_sync_to_async
    def mark_all_as_read(self, user_id):
        Notification.objects.filter(
            recipient_id=user_id,
            is_read=False
        ).update(is_read=True)
