from django.urls import path
from .views import UserWorkspacesView, WorkspaceCreateView

urlpatterns = [
    path("list/", UserWorkspacesView.as_view(), name="list-workspace"),
    path("create/", WorkspaceCreateView.as_view(), name="create-workspace"),
]
