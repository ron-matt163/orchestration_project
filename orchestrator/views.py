"""
REST endpoints for launching and monitoring orchestration jobs.
"""

import logging
from collections import defaultdict
from celery.result import AsyncResult
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from orchestrator.tasks import orchestrate_tasks

logger = logging.getLogger(__name__)
MAX_CONCURRENT_JOBS = 3
running_jobs: dict[str, set[str]] = defaultdict(set)

@api_view(["POST"])
def orchestrate(request, username: str):
    active = running_jobs[username]
    if len(active) >= MAX_CONCURRENT_JOBS:
        return Response(
            {"detail": f"User '{username}' already has {MAX_CONCURRENT_JOBS} running jobs."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    # Start the workflow and get the final task ID
    result = orchestrate_tasks.apply_async(args=[username])
    task_id = result.id
    active.add(task_id)

    return Response(
        {
            "message": "Orchestration started.",
            "task_id": task_id,
            "status_url": f"/status/{username}/{task_id}",
        },
        status=status.HTTP_202_ACCEPTED,
    )

@api_view(["GET"])
def job_status(request, username: str, task_id: str):
    async_res = AsyncResult(task_id)
    data = {"task_id": task_id, "state": async_res.state}

    if async_res.state == "SUCCESS":
        logger.info("Task %s completed with result type: %s", task_id, type(async_res.result))
        logger.info("Task %s result: %s", task_id, async_res.result)
        data["result"] = async_res.result
    elif async_res.state == "FAILURE":
        data["error"] = str(async_res.result)
    elif async_res.state == "PENDING":
        data["message"] = "Task is waiting for execution or unknown."
    elif async_res.state == "STARTED":
        data["message"] = "Task has been started."
    elif async_res.state == "RETRY":
        data["message"] = "Task is being retried."

    # free slot when job is done
    if async_res.ready() and task_id in running_jobs.get(username, set()):
        running_jobs[username].discard(task_id)
        if not running_jobs[username]:
            running_jobs.pop(username, None)

    return Response(data)
