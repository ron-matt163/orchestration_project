from django.db import models
from django.utils import timezone
from django.db.models.manager import Manager

class Job(models.Model):
    objects: Manager  # Type hint for the linter
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    job_id = models.CharField(max_length=36, unique=True)  # UUID
    username = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['username', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.username} - {self.job_id} - {self.status}"
        
    def mark_running(self):
        """Mark the job as running."""
        self.status = 'RUNNING'
        self.save()
        
    def mark_completed(self, result):
        """Mark the job as completed with the given result."""
        self.status = 'COMPLETED'
        self.result = result
        self.save()
        
    def mark_failed(self, error):
        """Mark the job as failed with the given error message."""
        self.status = 'FAILED'
        self.error = error
        self.save() 