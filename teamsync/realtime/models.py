from django.db import models
from accounts.models import Accounts
from workspace.models import Workspace

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