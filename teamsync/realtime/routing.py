from django.urls import re_path
from .consumers.notification_consumer import NotificationConsumer
from .consumers.chat_consumer import ChatConsumer
from .consumers.presence_consumer import PresenceConsumer
from .consumers.video_call_consumer import VideoCallConsumer

websocket_urlpatterns = [

      re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
      re_path(r'ws/chat/(?P<workspace_id>\d+)/(?P<receiver_id>\d+)/$', ChatConsumer.as_asgi()),
      re_path(r"ws/online/(?P<workspace_id>\d+)/?$", PresenceConsumer.as_asgi()),
      re_path(r'ws/video-call/$', VideoCallConsumer.as_asgi()),
      
]