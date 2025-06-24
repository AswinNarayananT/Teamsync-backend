from rest_framework.generics import CreateAPIView,  RetrieveAPIView, RetrieveUpdateAPIView,RetrieveUpdateDestroyAPIView, ListCreateAPIView, DestroyAPIView, UpdateAPIView
from rest_framework.views import APIView 
from .models import Project, Issue, Sprint, Attachment
from workspace.models import Workspace, WorkspaceMember, CustomRole
from .serializers import ProjectSerializer, IssueSerializer, IssueCreateSerializer, SprintSerializer, AttachmentSerializer, SprintWithIssuesSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from django.core.exceptions import ObjectDoesNotExist
from .permissions import HasWorkspacePermission
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from realtime.models import Notification
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
import cloudinary.uploader
from django.db.models import Q


class CompletedSprintsWithIssuesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        completed_sprints = Sprint.objects.filter(
            project_id=project_id,
            is_completed=True
        ).prefetch_related('issues', 'issues__assignee')  # optimize DB access

        serializer = SprintWithIssuesSerializer(completed_sprints, many=True)
        return Response(serializer.data)

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
    


class ProjectPermissionMixin:
    def get_object(self):
        obj = super().get_object()
        return obj



class ProjectUpdateView(ProjectPermissionMixin, UpdateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [HasWorkspacePermission]
    lookup_field = "id"
    lookup_url_kwarg = "project_id"
    required_permissions = ['update_project']  


class ProjectDeleteView(ProjectPermissionMixin, DestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [HasWorkspacePermission]
    lookup_field = "id"
    lookup_url_kwarg = "project_id"
    required_permissions = ['delete_project'] 



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
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        issues_qs = Issue.objects.filter(
            project_id=project_id,
            type__in=["task", "story", "bug"],
            is_completed=False
    )

        epic_params = request.query_params.getlist('epics')
        if epic_params:
            epic_ids = []
            include_none = False
            for e in epic_params:
                if str(e).lower() == 'none':
                    include_none = True
                elif str(e).isdigit():
                    epic_ids.append(int(e))

            parent_filter = Q()
            if epic_ids:
                parent_filter |= Q(parent_id__in=epic_ids)
            if include_none:
                parent_filter |= Q(parent__isnull=True)

            if parent_filter:
                issues_qs = issues_qs.filter(parent_filter)

        assignee_params = request.query_params.getlist('assignees')
        unassigned = request.query_params.get('unassigned') == 'true'
        assignee_filter = Q()

        if assignee_params:
            try:
                assignee_ids = [int(a) for a in assignee_params if str(a).isdigit()]
                if assignee_ids:
                    assignee_filter |= Q(assignee_id__in=assignee_ids)
            except ValueError:
                return Response({"detail": "Invalid assignee IDs"}, status=status.HTTP_400_BAD_REQUEST)

        if unassigned:
            assignee_filter |= Q(assignee__isnull=True)

        if assignee_filter:
            issues_qs = issues_qs.filter(assignee_filter)

        serializer = IssueSerializer(issues_qs, many=True)
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
        
        if request.user.id != membership.user_id:
            workspace = issue.project.workspace
            message = f"You've been assigned to issue: {issue.title}"
            notification = Notification.objects.create(
                recipient=membership.user,
                workspace=workspace,
                message=message
            )

            channel_layer = get_channel_layer()
            group_name = f"workspace_{workspace.id}_user_{membership.user.id}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_notification",
                    "content": {
                        "message": notification.message,
                        "workspace": {
                            "id": workspace.id,
                            "name": workspace.name,
                        },
                    }
                }
            )

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
            issue = Issue.objects.select_related("project__workspace", "assignee").get(id=issue_id)
        except Issue.DoesNotExist:
            return Response({"error": "Issue not found."}, status=status.HTTP_404_NOT_FOUND)

        current_workspace = issue.project.workspace

        try:
            member = WorkspaceMember.objects.get(workspace=current_workspace, user=request.user)
        except WorkspaceMember.DoesNotExist:
            return Response({"error": "You are not a member of this workspace."}, status=status.HTTP_403_FORBIDDEN)

        role = member.role

        if role in ["owner", "manager"]:
            issue.status = new_status
            issue.save()
            return Response({"issue_id": issue.id, "status": issue.status}, status=status.HTTP_200_OK)

        has_permission = False

        default_role_permissions = {
            "developer": ["update_status"],
            "designer": ["update_status"],
        }

        if role in default_role_permissions:
            has_permission = "update_status" in default_role_permissions[role]
        else:
            try:
                custom_role = CustomRole.objects.get(workspace=current_workspace, name=role)
                has_permission = "update_status" in custom_role.permissions
            except CustomRole.DoesNotExist:
                has_permission = False

        if not has_permission:
            return Response({"error": "You don't have permission to update status."}, status=status.HTTP_403_FORBIDDEN)

        if issue.assignee != request.user:
            return Response({"error": "You can only update status of issues assigned to you."}, status=status.HTTP_403_FORBIDDEN)

        issue.status = new_status
        issue.save()
        return Response({"issue_id": issue.id, "status": issue.status}, status=status.HTTP_200_OK)
    

class DeleteIssueView(DestroyAPIView):
    queryset = Issue.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def delete(self, request, *args, **kwargs):
        try:
            issue = self.get_object()
            issue_id = issue.id
            issue.delete()
            return Response({"id": issue_id, "detail": "Issue deleted successfully."}, status=status.HTTP_200_OK)
        except Issue.DoesNotExist:
            return Response({"error": "Issue not found."}, status=status.HTTP_404_NOT_FOUND)

class ProjectSprintListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
    queryset = Sprint.objects.all()
    serializer_class = SprintSerializer



class ActiveSprintIssueListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        active_sprints = Sprint.objects.filter(
            project_id=project_id,
            is_active=True,
            is_completed=False
        )

        sprint_ids = request.query_params.get("sprints")
        if sprint_ids:
            try:
                sprint_ids_list = [
                    int(pk) for pk in sprint_ids.split(",") if pk.strip().isdigit()
                ]
                filtered_sprints = active_sprints.filter(id__in=sprint_ids_list)
            except ValueError:
                return Response({"detail": "Invalid sprint IDs"}, status=400)
        else:
            filtered_sprints = active_sprints

        if not active_sprints.exists():
            return Response({"sprints": [], "issues": []})

        issues_qs = Issue.objects.filter(
            sprint__in=filtered_sprints,
            is_completed=False,
            type__in=["task", "story", "bug"]
        )

        parent_param = request.query_params.get("parents")
        if parent_param:
            tokens = [t.strip().lower() for t in parent_param.split(",")]
            numeric_ids = [int(t) for t in tokens if t.isdigit()]
            include_none = "none" in tokens

            parent_filter = Q()
            if numeric_ids:
                parent_filter |= Q(parent_id__in=numeric_ids)
            if include_none:
                parent_filter |= Q(parent__isnull=True)

            invalid = [t for t in tokens if not (t.isdigit() or t == "none")]
            if invalid:
                return Response(
                    {"detail": f"Invalid parent tokens: {invalid}"},
                    status=400
                )

            issues_qs = issues_qs.filter(parent_filter)

        assignee_param = request.query_params.get("assignee")
        if assignee_param:
            tokens = [t.strip().lower() for t in assignee_param.split(",")]
            numeric_ids = [int(t) for t in tokens if t.isdigit()]
            include_none = "none" in tokens

            assignee_filter = Q()
            if numeric_ids:
                assignee_filter |= Q(assignee__in=numeric_ids)
            if include_none:
                assignee_filter |= Q(assignee__isnull=True)

            invalid = [t for t in tokens if not (t.isdigit() or t == "none")]
            if invalid:
                return Response({"detail": f"Invalid assignee tokens: {invalid}"}, status=400)

            issues_qs = issues_qs.filter(assignee_filter)

        issue_data  = IssueSerializer(issues_qs,  many=True).data

        return Response({
            "issues":  issue_data,
        })



class AttachmentListCreateView(ListCreateAPIView):
    serializer_class = AttachmentSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        issue_id = self.kwargs['issue_id']
        return Attachment.objects.filter(issue_id=issue_id).order_by('-uploaded_at')

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        issue = get_object_or_404(Issue, id=self.kwargs['issue_id'])
        attachment_type = request.data.get('type')

        data = {
            'issue': issue.id,
            'type': attachment_type,
        }

        if attachment_type == 'link':
            url = request.data.get('url')
            if not url:
                return Response({'error': 'URL is required for link attachment.'},
                                status=status.HTTP_400_BAD_REQUEST)
            data['url'] = url

        elif attachment_type in ('file', 'image'):
            upload_file = request.FILES.get('file')
            if not upload_file:
                return Response({'error': 'File is required for file/image attachment.'},
                                status=status.HTTP_400_BAD_REQUEST)

            allowed = ['image/jpeg', 'image/png', 'application/pdf', 'image/webp']
            if upload_file.content_type not in allowed:
                return Response({
                    'error': f'Allowed types: {", ".join(allowed)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                result = cloudinary.uploader.upload(
                    upload_file,
                    folder="TeamSync",
                    resource_type="auto"
                )
                data['url'] = result.get('secure_url')
            except Exception as e:
                return Response({'error': f'Upload failed: {str(e)}'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response({'error': 'Invalid attachment type.'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            attachment = serializer.save()
            return Response(self.get_serializer(attachment).data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class AttachmentDeleteView(DestroyAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Attachment.objects.get(pk=self.kwargs['pk'])
        except Attachment.DoesNotExist:
            raise NotFound(detail="Attachment not found.")    



class SprintIssueStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, sprint_id):
        try:
            sprint = Sprint.objects.get(id=sprint_id)
        except Sprint.DoesNotExist:
            return Response({"detail": "Sprint not found."}, status=status.HTTP_404_NOT_FOUND)

        issues = Issue.objects.filter(sprint=sprint, type__in=["task", "story", "bug"], is_completed=False)
        total_issues = issues.count()
        

        incomplete_issues = issues.exclude(status="done")
        incomplete_count = incomplete_issues.count()

        data = {
            "sprint_id": sprint_id,
            "sprint_name": sprint.name,
            "total_issues": total_issues,
            "incomplete_issues": incomplete_count,
            "complete_issues": total_issues - incomplete_count,
            "all_done": incomplete_count == 0,
        }

        return Response(data, status=status.HTTP_200_OK)
    



class CompleteSprintAPIView(APIView):
    permission_classes = [IsAuthenticated,HasWorkspacePermission]
    required_permissions = ["complete_sprint"] 

    def post(self, request,project_id, sprint_id):
        try:
            sprint = Sprint.objects.get(id=sprint_id, is_active=True, is_completed=False)
        except Sprint.DoesNotExist:
            return Response({"detail": "Sprint not found or already inactive."}, status=status.HTTP_404_NOT_FOUND)

        issues = Issue.objects.filter(sprint=sprint)

        if not issues.exists():
            return Response({"detail": "Sprint must contain at least one issue to complete."}, status=status.HTTP_400_BAD_REQUEST)

        Issue.objects.filter(sprint=sprint, status="done").update(is_completed=True)

        incomplete_issues = issues.exclude(status="done")

        new_sprint = None

        if incomplete_issues.exists():
            action = request.data.get("action")
            if not action:
                return Response({"detail": "Action required for incomplete issues."}, status=status.HTTP_400_BAD_REQUEST)

            if action == "create_new":
                with transaction.atomic():
                    new_sprint = Sprint.objects.create(
                        name=f"{sprint.name}-Follow-up",
                        project=sprint.project,
                        is_active=False
                    )
                    incomplete_issues.update(sprint=new_sprint)

            elif action == "backlog":
                incomplete_issues.update(sprint=None)

            elif action == "move_to_another":
                target_sprint = Sprint.objects.filter(
                    project=sprint.project,
                    is_completed=False
                ).exclude(id=sprint.id).first()

                if target_sprint:
                    incomplete_issues.update(sprint=target_sprint)
                else:
                    incomplete_issues.update(sprint=None)

            else:
                return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

        sprint.is_completed = True
        sprint.is_active = False
        sprint.save()

        data = {"sprint_id": sprint.id}
        if new_sprint:
            data["new_sprint"] = SprintSerializer(new_sprint).data

        return Response(data, status=status.HTTP_200_OK)