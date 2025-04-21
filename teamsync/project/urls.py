from django.urls import path
from .views import CreateProjectView, WorkspaceProjectsAPIView, CreateIssueView, ProjectEpicsView ,ProjectIssuesView, AssignParentEpicView


urlpatterns = [
     path("create/", CreateProjectView.as_view(), name="create-project"),
     path('<int:workspace_id>/list/', WorkspaceProjectsAPIView.as_view(), name='workspace-projects'),
     path("<int:project_id>/issues/", CreateIssueView.as_view(), name="create-issue"),
     path('<int:project_id>/epics/', ProjectEpicsView.as_view(), name='project-epics'),
     path('<int:project_id>/issues/list/', ProjectIssuesView.as_view(), name='project-issues'),
     path('issue/assign-parent/', AssignParentEpicView.as_view(), name='assign-parent'),
]
