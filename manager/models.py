from django.db import models
from django.contrib.auth.models import User

# class Routine(models.Model):
#     REPEAT_CHOICES = [
#         ('once', 'Once'),
#         ('daily', 'Daily'),
#         ('weekly', 'Weekly'),
#     ]
    
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routines')
#     title = models.CharField(max_length=200)
#     time = models.TimeField()
#     repeat_type = models.CharField(
#         max_length=20,
#         choices=REPEAT_CHOICES,
#         default='once'
#     )
#     is_completed = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ['-created_at']
#         verbose_name = 'Routine'
#         verbose_name_plural = 'Routines'


#     def __str__(self):
#         return f"{self.title} at {self.time}"

class Routine(models.Model):
    REPEAT_CHOICES = [
        ('once', 'Once'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routines')
    title = models.CharField(max_length=200)
    time = models.TimeField()
    repeat_type = models.CharField(
        max_length=20,
        choices=REPEAT_CHOICES,
        default='once'
    )
    is_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  # Add this line
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Routine'
        verbose_name_plural = 'Routines'

    def __str__(self):
        return f"{self.title} at {self.time}"
    
class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Chat by {self.user.username} at {self.created_at}"