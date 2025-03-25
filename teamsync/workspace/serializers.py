from rest_framework import serializers
from .models import Workspace

class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ["id", "name", "workspace_type", "description", "work_type", "plan", "is_active", "plan_expiry", "created_at"]
    
    def create(self, validated_data):
        return Workspace.objects.create(**validated_data)