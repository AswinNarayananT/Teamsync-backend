from django.shortcuts import get_object_or_404
from workspace.models import Workspace
from project.models import Project
from django.urls import resolve

class WorkspaceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            resolver_match = resolve(request.path_info)
            workspace_id = resolver_match.kwargs.get("workspace_id")
            project_id = resolver_match.kwargs.get("project_id")

            if workspace_id:
                try:
                    request.current_workspace = Workspace.objects.get(id=workspace_id)
                except Workspace.DoesNotExist:
                    request.current_workspace = None
            elif project_id:
                try:
                    project = get_object_or_404(Project, id=project_id)
                    request.current_workspace = project.workspace
                except Project.DoesNotExist:
                    request.current_workspace = None
            else:
                request.current_workspace = None  

        except Exception as e:
            request.current_workspace = None

        return self.get_response(request)