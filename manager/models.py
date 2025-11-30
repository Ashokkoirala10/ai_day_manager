from django.db import models
from django.contrib.auth.models import User

class Routine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    time = models.TimeField()
    
    repeat_type = models.CharField(
        max_length=20,
        choices=[
            ('once', 'Once'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='once'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.time}"
