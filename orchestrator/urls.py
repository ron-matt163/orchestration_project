"""URL configuration for the orchestrator app."""

from django.urls import path
from orchestrator.views import orchestrate

urlpatterns = [
    path("orchestrate/", orchestrate),
]
