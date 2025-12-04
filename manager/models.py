from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Routine(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    REPEAT_CHOICES = [
        ('once', 'Once'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    CATEGORY_CHOICES = [
        ('work', 'Work'),
        ('personal', 'Personal'),
        ('health', 'Health'),
        ('study', 'Study'),
        ('shopping', 'Shopping'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    time = models.TimeField()
    date = models.DateField(default=timezone.now)
    
    # New fields for advanced features
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    repeat_type = models.CharField(max_length=20, choices=REPEAT_CHOICES, default='once')
    
    # Metadata
    estimated_duration = models.IntegerField(default=30, help_text="Duration in minutes")
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    reminder_sent = models.BooleanField(default=False)
    
    # For task breakdown
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtasks')
    order = models.IntegerField(default=0)
    
    # Tags for better organization
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'time', 'order']
        indexes = [
            models.Index(fields=['user', 'date', 'status']),
            models.Index(fields=['user', 'is_completed']),
        ]

    def __str__(self):
        return f"{self.title} at {self.time} ({self.get_priority_display()})"
    
    def mark_complete(self):
        """Mark task as completed"""
        self.is_completed = True
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def get_subtasks(self):
        """Get all subtasks for this task"""
        return self.subtasks.all()
    
    def has_subtasks(self):
        """Check if task has subtasks"""
        return self.subtasks.exists()


class UserPreference(models.Model):
    """Store user preferences and settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # Notification preferences
    enable_notifications = models.BooleanField(default=True)
    enable_voice_reminders = models.BooleanField(default=True)
    reminder_minutes_before = models.IntegerField(default=5)
    
    # Productivity settings
    work_start_time = models.TimeField(default='09:00')
    work_end_time = models.TimeField(default='17:00')
    preferred_task_duration = models.IntegerField(default=30)
    
    # AI preferences
    ai_auto_breakdown = models.BooleanField(default=True)
    ai_scheduling_suggestions = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user.username}"


class ProductivityLog(models.Model):
    """Track user productivity metrics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    
    tasks_created = models.IntegerField(default=0)
    tasks_completed = models.IntegerField(default=0)
    total_time_spent = models.IntegerField(default=0, help_text="Minutes")
    completion_rate = models.FloatField(default=0.0)
    
    # Peak productivity hour (0-23)
    peak_hour = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date}"
    
    def calculate_completion_rate(self):
        """Calculate and update completion rate"""
        if self.tasks_created > 0:
            self.completion_rate = (self.tasks_completed / self.tasks_created) * 100
        else:
            self.completion_rate = 0
        self.save()


class TaskNote(models.Model):
    """Notes attached to tasks"""
    task = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note for {self.task.title}"