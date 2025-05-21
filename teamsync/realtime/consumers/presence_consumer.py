import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from realtime.utils import (
    add_online_user,
    remove_online_user,
    is_user_online_in_workspace,
)

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
        await self.channel_layer.group_add(self.group_name, self.channel_name)
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

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "presence",
            "user_id": event["user_id"],
            "status": event["status"],
        }))

    @database_sync_to_async
    def add_user_to_cache(self):
        add_online_user(self.workspace_id, self.user.id)

    @database_sync_to_async
    def remove_user_from_cache(self):
        remove_online_user(self.workspace_id, self.user.id)

    @database_sync_to_async
    def check_user_online(self, user_id):
        return is_user_online_in_workspace(self.workspace_id, user_id)

