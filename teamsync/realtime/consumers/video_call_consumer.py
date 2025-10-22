from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging

logger = logging.getLogger(__name__)

class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user', None)
        self.group_name = None
        if not self.user or not self.user.is_authenticated:
            logger.warning("Unauthenticated user tried to connect to video call consumer")
            await self.close()
            return

        self.group_name = f'video_user_{self.user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

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
                f'video_user_{to_user_id}',
                {
                    'type': 'send_call_invite', 
                    'call_data': call_data,
                }
            )
        elif action == 'accept_call':
            room_id = data['room_id']
            # Extract caller ID from room_id (format: callerId_receiverId_timestamp)
            caller_id = room_id.split('_')[0]
            # Notify the caller that the call was accepted
            call_data = {
                'action': 'call_accepted',
                'room_id': room_id,
                'accepted_by': self.user.id,
            }
            await self.channel_layer.group_send(
                f'video_user_{caller_id}',
                {
                    'type': 'send_call_response',
                    'call_data': call_data,
                }
            )
        elif action == 'reject_call':
            room_id = data['room_id']
            # Extract caller ID from room_id (format: callerId_receiverId_timestamp)
            caller_id = room_id.split('_')[0]
            # Notify the caller that the call was rejected
            call_data = {
                'action': 'call_rejected',
                'room_id': room_id,
                'rejected_by': self.user.id,
            }
            await self.channel_layer.group_send(
                f'video_user_{caller_id}',
                {
                    'type': 'send_call_response',
                    'call_data': call_data,
                }
            )
        elif action == 'cancel_call':
            room_id = data['room_id']
            # Extract receiver ID from room_id (format: callerId_receiverId_timestamp)
            receiver_id = room_id.split('_')[1]
            # Notify the receiver that the call was cancelled
            call_data = {
                'action': 'call_cancelled',
                'room_id': room_id,
                'cancelled_by': self.user.id,
            }
            await self.channel_layer.group_send(
                f'video_user_{receiver_id}',
                {
                    'type': 'send_call_response',
                    'call_data': call_data,
                }
            )

    async def send_call_invite(self, event):
        await self.send(text_data=json.dumps(event['call_data']))

    async def send_call_response(self, event):
        await self.send(text_data=json.dumps(event['call_data']))

    async def chat_message_update(self, event):
        pass
