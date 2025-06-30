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


class Issue(models.Model):
    ISSUE_TYPES = [
        ("epic", "Epic"),
        ("story", "Story"),
        ("task", "Task"),
        ("bug", "Bug"),
        ("subtask", "Sub-task"),
    ]

    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("in_progress", "In Progress"),
        ("review", "In Review"),
        ("done", "Done"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=ISSUE_TYPES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo", db_index=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
        db_index=True
    )
    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="issues")
    sprint = models.ForeignKey("Sprint", null=True, blank=True, on_delete=models.SET_NULL, related_name="issues", db_index=True)

    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    is_completed = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["sprint", "is_completed", "type"]),
        ]

    def __str__(self):
        return f"{self.type.upper()}: {self.title}"


class Attachment(models.Model):
    ATTACHMENT_TYPES = [
        ("file", "File"),     
        ("link", "Link"),     
        ("image", "Image"),  
    ]

    issue = models.ForeignKey("Issue", on_delete=models.CASCADE, related_name="attachments")
    type = models.CharField(max_length=10, choices=ATTACHMENT_TYPES)
    url = models.URLField() 
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment ({self.type}) for {self.issue}"


class Sprint(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="sprints", db_index=True)
    name = models.CharField(max_length=255)
    goal = models.TextField(blank=True) 
    number = models.PositiveIntegerField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=False, db_index=True)
    is_completed = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('project', 'number') 
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["project", "is_active", "is_completed"]),
        ]

    def save(self, *args, **kwargs):
        if not self.pk:
            last_sprint = Sprint.objects.filter(project=self.project).order_by('-number').first()
            if last_sprint:
                self.number = last_sprint.number + 1
            else:
                self.number = 1

            project_name = self.project.name.replace(' ', '')  
            self.name = f"{project_name}-Sprint-{self.number}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"
