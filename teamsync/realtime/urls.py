from django.urls import path
from .views import ChatMessageListView,AuthValidationView, CreateMeetingView, UpcomingMeetingsView, RecentMeetingsView

urlpatterns = [
    path("auth/validate/", AuthValidationView.as_view(), name="auth-validate"),
    path('<int:workspace_id>/<int:receiver_id>/messages/', ChatMessageListView.as_view(), name='chat-message-list'),
    path('projects/<int:project_id>/meetings/create/', CreateMeetingView.as_view(), name='create-meeting'),
    path('workspaces/<int:workspace_id>/meetings/upcoming/', UpcomingMeetingsView.as_view(), name='workspace-upcoming-meetings'),
    path('workspaces/<int:workspace_id>/meetings/recent/', RecentMeetingsView.as_view(), name='workspace-recent-meetings'),

]
