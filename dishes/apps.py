from django.apps import AppConfig
import os


class DishesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dishes'

    def ready(self):
        # prevent duplicate scheduler (Django autoreload issue)
        if os.environ.get('RUN_MAIN') == 'true':
            from .scheduler import start_scheduler
            start_scheduler()