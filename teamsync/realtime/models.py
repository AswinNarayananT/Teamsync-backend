from django.db import models
from accounts.models import Accounts
from workspace.models import Workspace
import uuid
# Create your models here.


class Notification(models.Model):
    recipient = models.ForeignKey(Accounts, on_delete=models.CASCADE, related_name="notifications")
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.recipient} - {self.message[:50]}"
    

class ChatMessage(models.Model):
    sender = models.ForeignKey(Accounts, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(Accounts, related_name='received_messages', on_delete=models.CASCADE)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE, related_name='chat_messages')
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']    


class Meeting(models.Model):
    room_id = models.UUIDField(default=uuid.uuid4, unique=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    host = models.ForeignKey(Accounts, on_delete=models.CASCADE, related_name='hosted_meetings')
    participants = models.ManyToManyField(Accounts, related_name='meetings')
    start_time = models.DateTimeField()
    
    actual_start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    @property
    def actual_duration(self):
        if self.actual_start_time and self.end_time:
            return (self.end_time - self.actual_start_time).total_seconds() / 60
        return None
