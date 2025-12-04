from django.contrib import admin
from django.urls import path
from manager import views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),

    # Task Management
    path("task/add/", views.add_routine, name="add_routine"),
    path("task/delete/<int:id>/", views.delete_routine, name="delete_routine"),
    path("task/update/<int:id>/", views.update_routine, name="update_routine"),
    path("task/toggle/<int:id>/", views.toggle_complete, name="toggle_complete"),
    path("task/details/<int:id>/", views.get_task_details, name="task_details"),
    
    # Subtasks and Notes
    path("task/<int:parent_id>/subtask/add/", views.add_subtask, name="add_subtask"),
    path("task/<int:task_id>/note/add/", views.add_note, name="add_note"),

    # Chat System
    path("chat/", views.chat_ai, name="chat_ai"),
    path("chat/history/", views.chat_history, name="chat_history"),
    path("chat/clear/", views.chat_clear, name="chat_clear"),

    # Scheduler
    path("scheduler/start/", views.scheduler_start, name="start_scheduler"),
    path("scheduler/stop/", views.scheduler_stop, name="stop_scheduler"),
    path("scheduler/check/", views.scheduler_check, name="check_scheduler"),
    
    # Analytics
    path("stats/", views.productivity_stats, name="productivity_stats"),
]