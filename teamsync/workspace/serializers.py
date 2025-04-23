from rest_framework import serializers
from .models import Workspace, WorkspaceMember, CustomRole

class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ["id", "name", "workspace_type", "description", "work_type", "plan","stripe_subscription_id", "is_active", "is_blocked_by_admin", "plan_expiry", "created_at"]
    
    def create(self, validated_data):
        return Workspace.objects.create(**validated_data)
    

class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.first_name", read_only=True)
    # workspace = WorkspaceSerializer(read_only=True) 

    class Meta:
        model = WorkspaceMember
        fields = ["id", "user_email","user_id", "user_name", "role", "joined_at", "workspace"]
    


class CustomRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomRole
        fields = ['id', 'workspace', 'name', 'permissions']
        read_only_fields = ['id', 'workspace']
