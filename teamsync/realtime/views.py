from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import ChatMessage
from .serializers import ChatMessageSerializer
from workspace.models import Workspace
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# Create your views here.


class AuthValidationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"detail": "Token is valid."}, status=status.HTTP_200_OK)


class ChatMessageListView(ListAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        self.workspace_id = self.kwargs['workspace_id']
        self.receiver_id = self.kwargs['receiver_id']
        user = self.request.user

        Workspace.objects.get(id=self.workspace_id)

        messages = ChatMessage.objects.filter(
            workspace_id=self.workspace_id
        ).filter(
            Q(sender=user, receiver_id=self.receiver_id) |
            Q(sender_id=self.receiver_id, receiver=user)
        ).order_by('timestamp')

        # Mark unread messages received by the current user as read
        unread = messages.filter(receiver=user, is_read=False)
        self.unread_message_ids = list(unread.values_list('id', flat=True))
        unread.update(is_read=True)

        return messages

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if self.unread_message_ids:
            self.notify_sender_messages_read()
        return response

    def notify_sender_messages_read(self):
        channel_layer = get_channel_layer()
        room_name = self.get_room_name(self.request.user.id, self.receiver_id, self.workspace_id)

        async_to_sync(channel_layer.group_send)(
            f"chat_{room_name}",
            {
                "type": "read_update_event",
                "reader_id": self.request.user.id,
                "message_ids": self.unread_message_ids,
            }
        )

    @staticmethod
    def get_room_name(user1_id, user2_id, workspace_id):
        ordered = sorted([str(user1_id), str(user2_id)])
        return f"{ordered[0]}_{ordered[1]}_{workspace_id}"