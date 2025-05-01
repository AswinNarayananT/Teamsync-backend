from django.urls import re_path
from .consumers.notification_consumer import NotificationConsumer

websocket_urlpatterns = [

      re_path(r'ws/notifications/(?P<workspace_id>\d+)/$', NotificationConsumer.as_asgi()),

]