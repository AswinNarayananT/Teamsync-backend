from django.urls import path
from .views import UserWorkspacesView, WorkspaceCreateView, SendInvitesView, AcceptInviteView, WorkspaceMembersListView, StripeSubscriptionDetailView, CancelSubscriptionView,  WorkspaceStatusView, CreateCustomRoleView, CustomRoleListCreateView, CustomRoleUpdateView
from .stripe_webhook import StripeWebhookView

urlpatterns = [
    path("list/", UserWorkspacesView.as_view(), name="list-workspace"),
    path("create/", WorkspaceCreateView.as_view(), name="create-workspace"),
    path("send-invites/", SendInvitesView.as_view(), name="invite-member"),
    path("accept-invite/", AcceptInviteView.as_view(), name="accept-invite"),
    path("<int:workspace_id>/members/", WorkspaceMembersListView.as_view(), name="workspace-members"),
    path("webhook/stripe/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path("subscription/<str:subscription_id>/", StripeSubscriptionDetailView.as_view(), name="stripe-subscription-detail"),
    path("<int:workspace_id>/status/", WorkspaceStatusView.as_view(), name="workspace-status"),
    path("cancel-subscription/", CancelSubscriptionView.as_view(), name="cancel-subscription"),
    path("<int:workspace_id>/create-role/", CreateCustomRoleView.as_view(), name="create-role"),
    path('<int:workspace_id>/custom-roles/', CustomRoleListCreateView.as_view(), name="custom-role"),
    path('<int:workspace_id>/roles/<int:role_id>/', CustomRoleUpdateView.as_view(), name="update-role"), 
]
