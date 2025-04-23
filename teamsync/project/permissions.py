# teamsync/project/permissions.py

from rest_framework.permissions import BasePermission
from workspace.models import WorkspaceMember, CustomRole



class HasWorkspacePermission(BasePermission):
    def has_permission(self, request, view):
        required_permissions = getattr(view, 'required_permissions', [])
        current_workspace = getattr(request, 'current_workspace', None)
        print("Current workspace:", current_workspace)

        if not (request.user and request.user.is_authenticated):
            return False

        if not current_workspace:
            return False

        try:
            member = WorkspaceMember.objects.get(workspace=current_workspace, user=request.user)
        except WorkspaceMember.DoesNotExist:
            return False

        role = member.role

        default_role_permissions = {
            "owner": ["*"],
            "manager": ["create_epic", "start_sprint", "invite_members"],
            "developer": ["update_status", "view_board"],
            "designer": ["update_design_doc"],
        }

        if role in default_role_permissions:
            role_perms = default_role_permissions[role]
            return "*" in role_perms or all(p in role_perms for p in required_permissions)

        try:
            custom_role = CustomRole.objects.get(workspace=current_workspace, name=role)
            return all(p in custom_role.permissions for p in required_permissions)
        except CustomRole.DoesNotExist:
            return False


# class HasRoleInWorkspace(BasePermission):
#     def has_permission(self, request, view):
#         required_roles = getattr(view, 'required_roles', [])
#         current_workspace = getattr(request, 'current_workspace', None)
        

#         if not (request.user and request.user.is_authenticated):
#             print("User is not authenticated.")
#             return False

#         if not current_workspace:
#             print("Current workspace is missing.")
#             return False


#         # Check if the user has one of the required roles in the workspace
#         has_permission = WorkspaceMember.objects.filter(
#             workspace=current_workspace,
#             user=request.user,
#             role__in=required_roles
#         ).exists()

#         print(f"Has permission: {has_permission}")
#         return has_permission