import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from realtime.models import ChatMessage


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.receiver_id = int(self.scope["url_route"]["kwargs"]["receiver_id"])
        self.workspace_id = int(self.scope["url_route"]["kwargs"]["workspace_id"])

        self.room_group_name = f"chat_{self.get_room_name(self.user.id, self.receiver_id, self.workspace_id)}"

        if not self.user.is_authenticated or self.user.id == self.receiver_id:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.mark_messages_delivered()
        updated_message_ids = await self.mark_all_messages_read()
        print("Updated Message IDs", updated_message_ids)
        print(f"[mark_all_messages_read] Reader: {self.user.id}, Sender: {self.receiver_id}, Updated: {updated_message_ids}")

        if updated_message_ids:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "read_update_event",
                    "reader_id": self.user.id,
                    "message_ids": updated_message_ids,
                }
            )
            
            await self.update_unread_summary_for_user(self.user.id)
            await self.update_unread_summary_for_user(self.receiver_id)

        await self.send_previous_messages(offset=0, limit=20)

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type")

        if message_type == "chat_message":
            await self.handle_chat_message(data)
        elif message_type == "mark_read":
            message_ids = data.get("message_ids", [])
            await self.mark_messages_read(message_ids)
        elif message_type == "fetch_history":
            offset = data.get("offset", 0)
            limit = data.get("limit", 20)
            await self.mark_messages_delivered()
            await self.send_previous_messages(offset=offset, limit=limit)

    async def handle_chat_message(self, data):
        text = data.get("text", "").strip()
        if not text:
            return

        message = await self.save_message(
            sender=self.user.id,
            receiver=self.receiver_id,
            workspace_id=self.workspace_id,
            text=text
        )

        # Send message to the room group (both sender and receiver are in this group)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message_event",
                "message": {
                    "id": message["id"],
                    "sender": self.user.id,
                    "receiver": self.receiver_id,
                    "text": text,
                    "timestamp": message["timestamp"],
                    "is_read": False,
                    "is_delivered": False,
                }
            }
        )

        await self.update_unread_summary_for_user(self.receiver_id)

    async def chat_message_event(self, event):
        message = event["message"]

        if self.user.id == message["receiver"]:
            await self.mark_single_message_delivered(message["id"])

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "delivery_update_event",
                    "message_id": message["id"],
                    "receiver_id": self.user.id,
                }
            )

        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": message
        }))

    async def delivery_update_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "delivery_update",
            "message_id": event["message_id"],
            "receiver_id": event["receiver_id"],
        }))

    async def chat_message_update(self, event):
        await self.update_unread_summary_for_user(self.user.id)
    
    async def send_previous_messages(self, offset=0, limit=20):
        messages = await self.get_chat_history(offset=offset, limit=limit)
        total_count = await self.get_total_message_count()
        has_more = (offset + limit) < total_count
        
        await self.send(text_data=json.dumps({
            "type": "chat_history",
            "messages": messages,
            "offset": offset,
            "limit": limit,
            "has_more": has_more,
            "total_count": total_count
        }))

    async def mark_messages_delivered(self):
        await self.set_delivered(sender_id=self.receiver_id, receiver_id=self.user.id, workspace_id=self.workspace_id)

    async def mark_single_message_delivered(self, message_id):
        await self.set_single_delivered(message_id)
        await self.channel_layer.group_send(
            f"presence_workspace_{self.workspace_id}",
            {
                "type": "presence_read_update",
                "reader_id": self.user.id,
                "receiver_id": self.receiver_id,
                "workspace_id": self.workspace_id,
            }
        )

    async def mark_messages_read(self, message_ids):
        if not message_ids:
            return

        await self.set_read(message_ids)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "read_update_event", 
                "reader_id": self.user.id,
                "message_ids": message_ids,
            }
        )

        await self.channel_layer.group_send(
            f"presence_workspace_{self.workspace_id}",
            {
                "type": "presence_read_update",
                "reader_id": self.user.id,
                "receiver_id": self.receiver_id,
                "workspace_id": self.workspace_id,
            }
        )

        await self.update_unread_summary_for_user(self.user.id)
        await self.update_unread_summary_for_user(self.receiver_id)

    async def read_update_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "read_update",
            "reader_id": event["reader_id"],
            "message_ids": event["message_ids"],
        }))

    async def update_unread_summary_for_user(self, user_id):
        """Send unread summary update to a specific user"""
        await self.channel_layer.group_send(
            f"user_{user_id}",
            {
                "type": "chat_message_update",
                "receiver_id": user_id,
            }
        )

    @database_sync_to_async
    def save_message(self, sender, receiver, workspace_id, text):
        message = ChatMessage.objects.create(
            sender_id=sender,
            receiver_id=receiver,
            workspace_id=workspace_id,
            text=text,
            is_delivered=False,
            is_read=False
        )
        return {
            "id": message.id,
            "timestamp": message.timestamp.isoformat()
        }

    @database_sync_to_async
    def get_chat_history(self, offset=0, limit=20):
        # Get total count first
        total_count = ChatMessage.objects.filter(
            workspace_id=self.workspace_id,
            sender_id__in=[self.user.id, self.receiver_id],
            receiver_id__in=[self.user.id, self.receiver_id],
        ).count()
        
        if offset == 0:
            # Initial load: get the last 20 messages (newest at bottom)
            start_offset = max(0, total_count - limit)
        else:
            # Load more: get older messages above current ones
            # offset represents how many messages we've already loaded
            start_offset = max(0, total_count - limit - offset)
        
        qs = ChatMessage.objects.filter(
            workspace_id=self.workspace_id,
            sender_id__in=[self.user.id, self.receiver_id],
            receiver_id__in=[self.user.id, self.receiver_id],
        ).order_by("timestamp")[start_offset:start_offset + limit]

        return [
            {
                "id": msg.id,
                "sender": msg.sender_id,
                "receiver": msg.receiver_id,
                "text": msg.text,
                "timestamp": msg.timestamp.isoformat(),
                "is_read": msg.is_read,
                "is_delivered": msg.is_delivered,
            } for msg in qs
        ]

    @database_sync_to_async
    def get_total_message_count(self):
        return ChatMessage.objects.filter(
            workspace_id=self.workspace_id,
            sender_id__in=[self.user.id, self.receiver_id],
            receiver_id__in=[self.user.id, self.receiver_id],
        ).count()

    @database_sync_to_async
    def set_delivered(self, sender_id, receiver_id, workspace_id):
        ChatMessage.objects.filter(
            sender_id=sender_id,
            receiver_id=receiver_id,
            workspace_id=workspace_id,
            is_delivered=False
        ).update(is_delivered=True)

    @database_sync_to_async
    def set_single_delivered(self, message_id):
        ChatMessage.objects.filter(id=message_id, is_delivered=False).update(is_delivered=True)

    @database_sync_to_async
    def set_read(self, message_ids):
        ChatMessage.objects.filter(id__in=message_ids, is_read=False).update(is_read=True)

    @database_sync_to_async
    def mark_all_messages_read(self):
        qs = ChatMessage.objects.filter(
            sender_id=self.receiver_id,
            receiver_id=self.user.id,
            workspace_id=self.workspace_id,
            is_read=False
        )

        print("DEBUG --- Receiver ID:", self.receiver_id)
        print("DEBUG --- User ID:", self.user.id)
        print("DEBUG --- Workspace ID:", self.workspace_id)
        print("DEBUG --- Unread Count:", qs.count())

        message_ids = list(qs.values_list("id", flat=True))

        if message_ids:
            qs.update(is_read=True)

        return message_ids


    @staticmethod
    def get_room_name(user1, user2, workspace_id):
        sorted_ids = sorted([user1, user2])
        return f"{sorted_ids[0]}_{sorted_ids[1]}_{workspace_id}"

