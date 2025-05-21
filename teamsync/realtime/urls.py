from django.urls import path
from .views import ChatMessageListView,AuthValidationView

urlpatterns = [
    path("auth/validate/", AuthValidationView.as_view(), name="auth-validate"),
    path('<int:workspace_id>/<int:receiver_id>/messages/', ChatMessageListView.as_view(), name='chat-message-list'),

]
