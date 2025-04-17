from django.db import models
from django.conf import settings
from accounts.models import Accounts
from workspace.models import Workspace

# Create your models here.


class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='projects')
    owner = models.ForeignKey(Accounts, on_delete=models.SET_NULL, null=True, related_name='owned_projects')
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    is_completed = models.BooleanField(default=False)  
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('name', 'workspace')  
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.workspace.name})"