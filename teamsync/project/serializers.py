from rest_framework import serializers
from .models import Project

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = ["owner", "workspace", "created_at", "updated_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        workspace = self.context["request"].current_workspace 

        return Project.objects.create(
            owner=user,
            workspace=workspace,
            **validated_data
        )
