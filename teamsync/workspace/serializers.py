from rest_framework import serializers
from .models import Workspace, WorkspaceMember

class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ["id", "name", "workspace_type", "description", "work_type", "plan", "is_active", "plan_expiry", "created_at"]
    
    def create(self, validated_data):
        return Workspace.objects.create(**validated_data)
    

class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.first_name", read_only=True)
    workspace = WorkspaceSerializer(read_only=True)  # Include workspace details

    class Meta:
        model = WorkspaceMember
        fields = ["id", "user_email", "user_name", "role", "joined_at", "workspace"]
    