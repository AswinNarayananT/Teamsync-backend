# teamsync/project/permissions.py

from rest_framework.permissions import BasePermission
from workspace.models import WorkspaceMember


class HasRoleInWorkspace(BasePermission):
    def has_permission(self, request, view):
        required_roles = getattr(view, 'required_roles', [])
        current_workspace = getattr(request, 'current_workspace', None)
        
        # Log details for debugging
        print(f"Required Roles: {required_roles}")
        print(f"Current Workspace: {current_workspace}")
        print(f"Request User: {request.user}")

        if not (request.user and request.user.is_authenticated):
            print("User is not authenticated.")
            return False

        if not current_workspace:
            print("Current workspace is missing.")
            return False


        # Check if the user has one of the required roles in the workspace
        has_permission = WorkspaceMember.objects.filter(
            workspace=current_workspace,
            user=request.user,
            role__in=required_roles
        ).exists()

        print(f"Has permission: {has_permission}")
        return has_permission