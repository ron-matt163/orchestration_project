"""URL configuration for the orchestrator app."""
from django.urls import path
from orchestrator import views

urlpatterns = [
    path("orchestrate/<str:username>", views.orchestrate, name="orchestrate"),
    path("status/<str:username>/<str:job_id>", views.job_status, name="job_status"),
]
