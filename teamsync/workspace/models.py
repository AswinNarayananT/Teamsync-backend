from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from datetime import timedelta
from adminpanel.models import Plan

# Create your models here.


User = get_user_model()

class Workspace(models.Model):
    WORKSPACE_TYPES = [
        ("individual", "Individual"),
        ("company", "Company"),
    ]

    WORK_TYPES = [
        ("software_development", "Software Development"),
        ("design", "Design"),
        ("product_management", "Product Management"),
        ("marketing", "Marketing"),
        ("project_management", "Project Management"),
        ("finance", "Finance"),
    ]

    name = models.CharField(max_length=255)
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="workspace")
    workspace_type = models.CharField(max_length=20, choices=WORKSPACE_TYPES, default="individual")  
    work_type = models.CharField(max_length=50, choices=WORK_TYPES, default="software_development")  
    description = models.TextField(blank=True, null=True)  
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)  
    is_blocked_by_admin = models.BooleanField(default=False)  
    plan_expiry = models.DateTimeField(null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.plan and not self.plan_expiry:
            self.plan_expiry = now() + timedelta(days=self.plan.duration_days)
            self.is_active = True 

        if self.is_blocked_by_admin:  
            self.is_active = False
        
        super().save(*args, **kwargs)

    def is_plan_active(self):
        return self.plan_expiry and self.plan_expiry > now()

    def deactivate_workspace(self):
        self.is_active = False
        self.save()

    def block_by_admin(self):
        self.is_blocked_by_admin = True
        self.is_active = False
        self.save()

    def unblock_by_admin(self):
        self.is_blocked_by_admin = False
        self.is_active = self.is_plan_active() 
        self.save()

    def __str__(self):
        return f"{self.name} ({'Blocked' if self.is_blocked_by_admin else 'Active' if self.is_plan_active() else 'Expired'})"


class WorkspaceMember(models.Model):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("manager", "Manager"),
        ("developer", "Developer"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="members")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="developer")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "workspace"]  

    def __str__(self):
        return f"{self.user.email} - {self.role} in {self.workspace.name}"


class WorkspaceInvitation(models.Model):
    ROLE_CHOICES = [
        ("manager", "Manager"),
        ("developer", "Developer"),
    ]

    email = models.EmailField()
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="invitations")
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="developer") 
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invite: {self.email} to {self.workspace.name} as {self.role}"