from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView 
from .models import Project, Issue
from workspace.models import Workspace
from .serializers import ProjectSerializer, IssueSerializer, IssueCreateSerializer
from .permissions import HasRoleInWorkspace
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
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



class CreateIssueView(CreateAPIView):
    queryset = Issue.objects.all()
    serializer_class = IssueCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        project_id = self.kwargs.get("project_id")
        serializer.save(project_id=project_id)




class ProjectEpicsView(APIView):
    def get(self, request, project_id):
        epics = Issue.objects.filter(project_id=project_id, type="epic")
        serializer = IssueSerializer(epics, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)        
    

class ProjectIssuesView(APIView):
    def get(self, request, project_id):
        issues = Issue.objects.filter(project_id=project_id, type__in=["task", "story", "bug"])
        serializer = IssueSerializer(issues, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class AssignParentEpicView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        issue_id = request.data.get('issue_id')
        epic_id = request.data.get('epic_id')

        try:
            issue = Issue.objects.get(id=issue_id)
            epic = Issue.objects.get(id=epic_id)

            if issue.type == 'epic':
                return Response({'error': 'Cannot assign a parent to an epic'}, status=400)

            issue.parent = epic
            issue.save()

            return Response({'message': 'Parent epic assigned successfully'})
        
        except Issue.DoesNotExist:
            return Response({'error': 'Issue or Epic not found'}, status=404)