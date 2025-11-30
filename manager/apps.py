import os
from django.apps import AppConfig


class ManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'manager'

    def ready(self):
        # Start scheduler ONLY after migrations + only when runserver starts
        if os.environ.get('RUN_MAIN') == 'true':
            from .scheduler.scheduler import start_scheduler
            start_scheduler()
