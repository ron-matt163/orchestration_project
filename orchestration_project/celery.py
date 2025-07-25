"""Celery configuration for the orchestration project."""

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "orchestration_project.settings")

app = Celery("orchestration_project")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.task_join_will_block = True

app.autodiscover_tasks()
