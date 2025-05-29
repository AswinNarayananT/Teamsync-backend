import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from realtime.models import ChatMessage
from django.db.models import Count, Q

User = get_user_model()

class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user", AnonymousUser())
        if not self.user.is_authenticated:
            await self.close()
            return

        self.workspace_id = self.scope["url_route"]["kwargs"].get("workspace_id")
        if not self.workspace_id:
            await self.close()
            return

        self.group_name = f"workspace_{self.workspace_id}_online"
        self.user_group = f"user_{self.user.id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.accept()

        await self.add_user_to_cache()

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "user_status",
                "user_id": self.user.id,
                "status": "online",
            },
        )

    async def disconnect(self, close_code):
        if hasattr(self, "workspace_id"):
            await self.remove_user_from_cache()

            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "user_status",
                    "user_id": self.user.id,
                    "status": "offline",
                },
            )
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            await self.channel_layer.group_discard(self.user_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get("type") == "check_user":
            target_user_id = data.get("user_id")
            if not target_user_id:
                return
            is_online = await self.check_user_online(target_user_id)
            await self.send(text_data=json.dumps({
                "type": "presence_check",
                "user_id": target_user_id,
                "status": "online" if is_online else "offline",
            }))

        elif data.get("type") == "get_unread_summary":
            summary = await self.get_unread_summary_with_last_message()
            await self.send(text_data=json.dumps({
                "type": "unread_summary",
                "data": summary,
            }))

        elif data.get("type") == "mark_read":
            sender_id = data.get("sender_id")
            if sender_id:
                await self.mark_messages_as_read(sender_id)

                # Send updated unread summary to receiver (self)
                summary = await self.get_unread_summary_with_last_message()
                await self.send(text_data=json.dumps({
                    "type": "unread_summary",
                    "data": summary,
                }))

                # Notify sender's WebSocket to refresh summary
                await self.channel_layer.group_send(
                    f"user_{sender_id}",
                    {
                        "type": "chat_message_update",
                        "receiver_id": sender_id,  # This is required by handler
                    }
                )

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "presence",
            "user_id": event["user_id"],
            "status": event["status"],
        }))

    async def chat_message_update(self, event):
        # This function is triggered via group_send to user_{id}
        if self.user.id != event.get("receiver_id"):
            return

        summary = await self.get_unread_summary_with_last_message()
        await self.send(text_data=json.dumps({
            "type": "unread_summary",
            "data": summary,
        }))

    async def presence_read_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "presence_read_update",
            "reader_id": event["reader_id"],
            "receiver_id": event["receiver_id"],
            "workspace_id": event["workspace_id"],
        }))
        

    @database_sync_to_async
    def add_user_to_cache(self):
        from realtime.utils import add_online_user
        add_online_user(self.workspace_id, self.user.id)

    @database_sync_to_async
    def remove_user_from_cache(self):
        from realtime.utils import remove_online_user
        remove_online_user(self.workspace_id, self.user.id)

    @database_sync_to_async
    def check_user_online(self, user_id):
        from realtime.utils import is_user_online_in_workspace
        return is_user_online_in_workspace(self.workspace_id, user_id)

    @database_sync_to_async
    def get_unread_summary_with_last_message(self):
        messages = ChatMessage.objects.filter(
            workspace_id=self.workspace_id
        ).filter(
            Q(sender=self.user) | Q(receiver=self.user)
        ).order_by('-timestamp')

        latest_msgs = {}

        for msg in messages:
            if msg.sender == self.user:
                other = msg.receiver
                from_self = True
            else:
                other = msg.sender
                from_self = False

            if other.id not in latest_msgs:
                latest_msgs[other.id] = {
                    'user_id': other.id,
                    'username': other.first_name,
                    'message': msg.text,
                    'timestamp': msg.timestamp.isoformat(),
                    'from_self': from_self,
                }

        unread_qs = ChatMessage.objects.filter(
            receiver=self.user,
            workspace_id=self.workspace_id,
            is_read=False
        ).values('sender_id').annotate(total=Count('id'))

        unread_count = {row['sender_id']: row['total'] for row in unread_qs}

        result = []
        for user_id, msg_data in latest_msgs.items():
            msg_data['unread_count'] = unread_count.get(user_id, 0)
            result.append(msg_data)

        return result

    @database_sync_to_async
    def mark_messages_as_read(self, sender_id):
        ChatMessage.objects.filter(
            sender_id=sender_id,
            receiver=self.user,
            workspace_id=self.workspace_id,
            is_read=False
        ).update(is_read=True)
