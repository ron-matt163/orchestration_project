"""
REST endpoints for launching and monitoring orchestration jobs.
"""

import logging
import uuid
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models.manager import Manager
from django.core.exceptions import ObjectDoesNotExist

from orchestrator.tasks import orchestrate_tasks
from orchestrator.models import Job

# Type hints for linter
Job.objects: Manager
Job.DoesNotExist: ObjectDoesNotExist

logger = logging.getLogger(__name__)
MAX_CONCURRENT_JOBS = 3

@api_view(["POST"])
def orchestrate(request, username: str):
    # Check for active jobs
    active_jobs = Job.objects.filter(username=username, status__in=['PENDING', 'RUNNING']).count()
    if active_jobs >= MAX_CONCURRENT_JOBS:
        return Response(
            {"detail": f"User '{username}' already has {MAX_CONCURRENT_JOBS} running jobs."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    # Create new job
    job_id = str(uuid.uuid4())
    job = Job.objects.create(
        job_id=job_id,
        username=username,
        status='PENDING'
    )

    # Start the workflow
    orchestrate_tasks.delay(username, job_id)

    return Response(
        {
            "message": "Orchestration started.",
            "job_id": job_id,
            "status_url": f"/status/{username}/{job_id}",
        },
        status=status.HTTP_202_ACCEPTED,
    )

@api_view(["GET"])
def job_status(request, username: str, job_id: str):
    try:
        job = Job.objects.get(job_id=job_id, username=username)
    except Job.DoesNotExist:
        return Response(
            {"detail": "Job not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    data = {
        "job_id": job.job_id,
        "status": job.status,
        "created_at": job.created_at,
        "updated_at": job.updated_at
    }

    if job.status == 'COMPLETED':
        data["result"] = job.result
    elif job.status == 'FAILED':
        data["error"] = job.error

    return Response(data)
