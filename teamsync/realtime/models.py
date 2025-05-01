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