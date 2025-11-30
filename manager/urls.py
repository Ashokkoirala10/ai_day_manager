from django.contrib import admin
from django.urls import path
from manager import views

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("add/", views.add_routine, name="add_routine"),
    path("delete/<int:id>/", views.delete_routine, name="delete_routine"),

    path("chat/", views.chat_ai, name="chat_ai"),

    path("scheduler/start/", views.scheduler_start, name="start_scheduler"),
    path("scheduler/stop/", views.scheduler_stop, name="stop_scheduler"),
    path("register/", views.register_view, name="register"),
    


]
