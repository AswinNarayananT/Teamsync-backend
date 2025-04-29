from rest_framework.generics import CreateAPIView,  RetrieveAPIView, RetrieveUpdateAPIView,RetrieveUpdateDestroyAPIView, ListCreateAPIView, ListAPIView
from rest_framework.views import APIView 
from .models import Project, Issue, Sprint
from workspace.models import Workspace, WorkspaceMember
from .serializers import ProjectSerializer, IssueSerializer, IssueCreateSerializer, SprintSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from django.core.exceptions import ObjectDoesNotExist
from .permissions import HasWorkspacePermission


# Create your views here.


class CreateProjectView(CreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated,HasWorkspacePermission]
    required_permissions = ["create_project"] 

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        project_id = self.kwargs.get("project_id")
        project = get_object_or_404(Project, id=project_id)
        serializer.save(project=project)


class IssueDetailView(RetrieveAPIView):
    queryset = Issue.objects.select_related('project', 'assignee').prefetch_related('attachments')
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_object(self):
        try:
            return self.get_queryset().get(**{self.lookup_field: self.kwargs[self.lookup_field]})
        except ObjectDoesNotExist:
            raise NotFound("Issue not found")
        


class IssueDetailUpdateView(RetrieveUpdateAPIView):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated]  
    
    def get(self, request, *args, **kwargs):
        issue = self.get_object()
        serializer = self.get_serializer(issue)
        return Response(serializer.data)
    
    def put(self, request, *args, **kwargs):
        issue = self.get_object()
        serializer = self.get_serializer(issue, data=request.data, partial=True)  

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)



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

            return Response({
                'issue_id': issue.id,
                'epic_id': epic.id,
            }, status=200)
        
        except Issue.DoesNotExist:
            return Response({'error': 'Issue or Epic not found'}, status=404)
        


class AssignAssigneeToIssueView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, issue_id):
        membership_id = request.data.get("member_id")
        if not membership_id:
            return Response({"error": "member_id is required"},
                            status=status.HTTP_400_BAD_REQUEST)

        membership = get_object_or_404(WorkspaceMember, id=membership_id)
        issue_qs = Issue.objects.filter(id=issue_id)
        issue = get_object_or_404(issue_qs, id=issue_id)

        if membership.workspace_id != issue.project.workspace_id:
            return Response({"error": "User is not part of the workspace."},
                            status=status.HTTP_403_FORBIDDEN)

        updated = issue_qs.update(assignee_id=membership.user_id)
        if not updated:
            return Response({"error": "Failed to assign assignee."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {"id": issue_id, "assignee": membership.user_id},
            status=status.HTTP_200_OK
        )
    


class UpdateIssueStatusView(APIView):
    permission_classes = [IsAuthenticated]  

    def patch(self, request, *args, **kwargs):
        issue_id = kwargs.get("issue_id")
        new_status = request.data.get("status")

        if new_status not in ["todo", "in_progress", "review", "done"]:
            return Response({"error": "Invalid status value."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            issue = Issue.objects.get(id=issue_id)
        except Issue.DoesNotExist:
            return Response({"error": "Issue not found."}, status=status.HTTP_404_NOT_FOUND)

        issue.status = new_status
        issue.save()

        return Response({"issue_id": issue.id, "status": issue.status}, status=status.HTTP_200_OK)




class ProjectSprintListCreateView(ListCreateAPIView):
    serializer_class = SprintSerializer

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return Sprint.objects.filter(project_id=project_id, is_completed=False).order_by('number')

    def perform_create(self, serializer):
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, id=project_id)

        latest_sprint = Sprint.objects.filter(project=project).order_by('-number').first()
        next_number = (latest_sprint.number + 1) if latest_sprint else 1

        serializer.save(project=project, number=next_number)

class SprintDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Sprint.objects.all()
    serializer_class = SprintSerializer


class ActiveSprintIssueListView(ListAPIView):
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')

        try:
            sprint = Sprint.objects.get(project_id=project_id, is_active=True)
        except Sprint.DoesNotExist:
            raise NotFound("No active sprint found for this project.")

        return Issue.objects.filter(sprint=sprint)



