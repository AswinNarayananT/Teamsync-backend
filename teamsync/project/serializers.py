from rest_framework import serializers
from .models import Project, Issue 

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





class IssueCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = ['id', 'title', 'description', 'type', 'parent', 'status']

    def validate(self, data):
        issue_type = data.get("type") or self.instance.type
        parent = data.get("parent") or getattr(self.instance, "parent", None)

        if parent and parent.id == self.instance.id:
            raise serializers.ValidationError("An issue cannot be its own parent.")

        if parent and parent.type != "epic":
            raise serializers.ValidationError("Parent must be an epic.")

        return data


class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = "__all__"

    def validate(self, data):
        issue_type = data.get("type") or self.instance.type
        parent = data.get("parent") or getattr(self.instance, "parent", None)

        if parent and parent.id == self.instance.id:
            raise serializers.ValidationError("An issue cannot be its own parent.")

        if parent and parent.type != "epic":
            raise serializers.ValidationError("Parent must be an epic.")

        return data
