from rest_framework import serializers
from accounts.models import Accounts
from .models import ChatMessage, Meeting

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'


class MeetingSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(many=True, queryset=Accounts.objects.all())
    workspace = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Meeting
        fields = [
            'id', 'room_id', 'workspace', 'host',
            'participants', 'start_time', 'actual_start_time', 'end_time', 'actual_duration'
        ]
        read_only_fields = ['id', 'room_id', 'host', 'actual_start_time', 'end_time', 'actual_duration']
    
    def create(self, validated_data):
        participants = validated_data.pop('participants', [])
        meeting = Meeting.objects.create(**validated_data)
        meeting.participants.set(participants)
        return meeting


class MeetingListSerializer(serializers.ModelSerializer):
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    host_name = serializers.CharField(source='host.full_name', read_only=True)

    class Meta:
        model = Meeting
        fields = ['id', 'room_id', 'start_time', 'end_time', 'workspace_name', 'host_name']