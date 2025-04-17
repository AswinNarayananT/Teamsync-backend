from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView 
from .models import Project
from workspace.models import Workspace
from .serializers import ProjectSerializer
from .permissions import HasRoleInWorkspace
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404



# Create your views here.


class CreateProjectView(CreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, HasRoleInWorkspace]
    required_roles = ["owner", "Manager"]  

    def initial(self, request, *args, **kwargs):

        workspace_id = request.data.get("workspaceId")

        try:
            request.current_workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            request.current_workspace = None

        return super().initial(request, *args, **kwargs)

    def get_queryset(self):
        return Project.objects.filter(workspace=self.request.current_workspace)



class WorkspaceProjectsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, id=workspace_id)


        projects = Project.objects.filter(workspace=workspace).order_by("-created_at")  
        serialized_projects = ProjectSerializer(projects, many=True).data

        if projects.exists():
            request.session["current_project_id"] = projects.first().id

        return Response({
            "projects": serialized_projects,
            "current_project_id": request.session.get("current_project_id")
        }, status=status.HTTP_200_OK)
