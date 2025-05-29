from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
import json
import logging
logger = logging.getLogger(__name__)

class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user', None)
        self.group_name = None
        logger.info(f"Connecting user: {self.user}")
        if not self.user or not self.user.is_authenticated:
            logger.warning("Unauthenticated user tried to connect")
            await self.close()
            return

        self.group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info(f"User {self.user} connected to group {self.group_name}")

    async def disconnect(self, close_code):
        user_str = getattr(self, 'user', None)
        group_name = getattr(self, 'group_name', None)
        logger.info(f"Disconnecting user {user_str} from group {group_name}")
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'call_user':
            to_user_id = data['to_user_id']
            call_data = {
                'action': 'incoming_call',
                'from_user_id': self.user.id,
                'from_user_name': self.user.first_name,
                'room_id': data['room_id'],
            }
            await self.channel_layer.group_send(
                f'user_{to_user_id}',
                {
                    'type': 'send_call_invite',
                    'call_data': call_data,
                }
            )

        elif action == 'missed_call':
            pass

    async def send_call_invite(self, event):
        await self.send(text_data=json.dumps(event['call_data']))