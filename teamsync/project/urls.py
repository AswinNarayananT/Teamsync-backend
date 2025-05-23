from django.urls import path
from .views import CreateProjectView, WorkspaceProjectsAPIView, CreateIssueView, ProjectEpicsView ,ProjectIssuesView, AssignParentEpicView, AssignAssigneeToIssueView, UpdateIssueStatusView, IssueDetailUpdateView,ProjectSprintListCreateView,SprintDetailView,ActiveSprintIssueListView, AttachmentListCreateView, AttachmentDeleteView, ProjectDeleteView,ProjectUpdateView, SprintIssueStatusView,CompleteSprintAPIView


urlpatterns = [
     path("create/", CreateProjectView.as_view(), name="create-project"),
     path('<int:project_id>/update/', ProjectUpdateView.as_view(), name='project-update'),
     path('<int:project_id>/delete/', ProjectDeleteView.as_view(), name='project-delete'),
     path('<int:workspace_id>/list/', WorkspaceProjectsAPIView.as_view(), name='workspace-projects'),
     path("<int:project_id>/issues/", CreateIssueView.as_view(), name="create-issue"),
     path('<int:project_id>/epics/', ProjectEpicsView.as_view(), name='project-epics'),
     path('<int:project_id>/issues/list/', ProjectIssuesView.as_view(), name='project-issues'),
     path('issue/assign-parent/', AssignParentEpicView.as_view(), name='assign-parent'),
     path('issue/<int:issue_id>/assign-assignee/', AssignAssigneeToIssueView.as_view(), name='assign-assignee'),
     path('issue/<int:issue_id>/status/', UpdateIssueStatusView.as_view(), name='update-issue-status'),
     path("issue/<int:pk>/", IssueDetailUpdateView.as_view(), name="issue-detail"),
     path('<int:project_id>/sprints/', ProjectSprintListCreateView.as_view(), name='project-sprint-list-create'),
     path('sprints/<int:pk>/', SprintDetailView.as_view(), name='sprint-detail'),
     path('<int:project_id>/active-sprint-issues/', ActiveSprintIssueListView.as_view(), name='active-sprint-issues'),
     path("sprints/<int:sprint_id>/issues/", SprintIssueStatusView.as_view(), name="sprint-issue-status"),
     path('sprints/<int:sprint_id>/complete/', CompleteSprintAPIView.as_view(), name='complete-sprint'),
     path('issues/<int:issue_id>/attachments/', AttachmentListCreateView.as_view(), name='attachment-list-create'),
     path('attachments/<int:pk>/', AttachmentDeleteView.as_view(), name='attachment-delete'),
]
