from django.apps import AppConfig


class ManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'manager'
    def ready(self):
        # Auto-start scheduler
        from .scheduler.scheduler import start_scheduler
        start_scheduler()