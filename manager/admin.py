from django.contrib import admin
from .models import Routine, ChatMessage

# Register your models here.
@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'time', 'repeat_type', 'is_completed',  'created_at']
    list_filter = ['repeat_type', 'is_completed', 'created_at']
    search_fields = ['title', 'user__username']
    date_hierarchy = 'created_at'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'message', 'response']
    date_hierarchy = 'created_at'