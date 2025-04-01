from django.urls import path
from .views import UserWorkspacesView, WorkspaceCreateView, SendInvitesView, AcceptInviteView

urlpatterns = [
    path("list/", UserWorkspacesView.as_view(), name="list-workspace"),
    path("create/", WorkspaceCreateView.as_view(), name="create-workspace"),
    path("send-invites/", SendInvitesView.as_view(), name="invite-member"),
    path("accept-invite/", AcceptInviteView.as_view(), name="accept-invite"),
]
