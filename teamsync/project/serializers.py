from rest_framework import serializers
from .models import Project, Issue ,Attachment

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

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'type', 'file', 'link', 'uploaded_at']


class IssueCreateSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, required=False)

    class Meta:
        model = Issue
        fields = ['id', 'title', 'description', 'type', 'parent', 'status', 'project', 'assignee', 'start_date', 'end_date', 'attachments']
        read_only_fields = ['project'] 
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True},
            'parent': {'required': False},
            'status': {'required': False},
            'assignee': {'required': False},
            'project': {'required': True}, 
            'start_date': {'required': False},
            'end_date': {'required': False},
        }

    def validate(self, data):
        issue_type = data.get("type") or getattr(self.instance, "type", None)
        parent = data.get("parent") or getattr(self.instance, "parent", None)

        if parent and self.instance and parent.id == self.instance.id:
            raise serializers.ValidationError("An issue cannot be its own parent.")

        if parent and parent.type != "epic":
            raise serializers.ValidationError("Parent must be an epic.")

        return data

    def create(self, validated_data):
        attachments_data = validated_data.pop("attachments", [])
        issue = Issue.objects.create(**validated_data)

        for attachment in attachments_data:
            Attachment.objects.create(issue=issue, **attachment)

        return issue
    





class IssueSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)
    
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
