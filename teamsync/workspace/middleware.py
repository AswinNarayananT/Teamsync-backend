from django.urls import resolve
from workspace.models import Workspace

class WorkspaceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            resolver_match = resolve(request.path_info)
            workspace_id = resolver_match.kwargs.get("workspace_id")
            if workspace_id:
                try:
                    request.current_workspace = Workspace.objects.get(id=workspace_id)
                except Workspace.DoesNotExist:
                    request.current_workspace = None
        except Exception as e:
            request.current_workspace = None

        return self.get_response(request)