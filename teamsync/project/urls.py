from django.urls import path
from .views import CreateProjectView, WorkspaceProjectsAPIView


urlpatterns = [
     path("create/", CreateProjectView.as_view(), name="create-project"),
     path('<int:workspace_id>/list/', WorkspaceProjectsAPIView.as_view(), name='workspace-projects'),
]
