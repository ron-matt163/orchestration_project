import random
import time
import logging
import uuid
import json
from celery import shared_task, group, chord, chain
from orchestrator.models import Job
from django.db.models.manager import Manager
from celery.result import AsyncResult
from celery.canvas import signature

# Type hint for linter
Job.objects: Manager

logger = logging.getLogger(__name__)

@shared_task
def run_task(task_id, base_value=None):
    try:
        time.sleep(random.randint(1, 3))
        n = random.randint(100, 999)
        if base_value is not None:
            n += base_value
        return {"task_id": task_id, "result": n}
    except Exception as e:
        logger.error("Error in run_task: %s", e)
        raise

@shared_task
def aggregate(batch_results, username=None):
    time.sleep(30)
    total = sum(x["result"] for x in batch_results)
    return {
        "aggregated_sum": total,
        "username": username
    }

@shared_task
def create_second_batch(agg_result, job_id):
    """Creates the second batch of tasks with the base value from first aggregation."""
    try:
        logger.info("Received agg_result: %s (type: %s)", agg_result, type(agg_result))
        
        # Get username from aggregation result
        if isinstance(agg_result, dict):
            username = agg_result.get("username")
            base = agg_result["aggregated_sum"] // 5
        else:
            # Try to parse as JSON if it's a string
            try:
                if isinstance(agg_result, str):
                    agg_result = json.loads(agg_result)
                    username = agg_result.get("username")
                    base = agg_result["aggregated_sum"] // 5
                else:
                    raise ValueError(f"Unexpected result type: {type(agg_result)}")
            except json.JSONDecodeError as e:
                logger.error("Failed to parse result as JSON: %s", e)
                # Update job status to failed
                job = Job.objects.get(job_id=job_id)
                job.status = 'FAILED'
                job.error = f"Failed to parse aggregation result: {str(e)}"
                job.save()
                raise
        
        if not username:
            raise ValueError("Username not found in aggregation result")
        
        # Create the second batch group
        second_batch = group(run_task.s(f"{username}-b2-{i}", base) for i in range(5))
        
        # Create the chord for the second batch
        logger.info("Creating chord for second batch with base: %s", base)
        return {
            "chord": chord(second_batch, aggregate.s(username=username)),
            "first_agg": agg_result
        }
    except Exception as e:
        # Update job status to failed
        job = Job.objects.get(job_id=job_id)
        job.status = 'FAILED'
        job.error = str(e)
        job.save()
        raise

@shared_task
def run_second_batch(batch_data, job_id):
    """Runs the second batch and chains to finalize_results."""
    try:
        logger.info("Starting run_second_batch with batch_data: %s", batch_data)
        chord_data = batch_data["chord"]
        first_agg = batch_data["first_agg"]
        
        # Reconstruct the chord from the data
        header = [signature(task) for task in chord_data["kwargs"]["header"]]
        body = signature(chord_data["kwargs"]["body"])
        chord_obj = chord(header, body)
        
        # Create a chain that will run the chord and then finalize
        workflow = chain(
            chord_obj,
            finalize_results.s(job_id=job_id, first_agg=first_agg)
        )
        
        # Start the workflow
        workflow.apply_async()
        
    except Exception as e:
        logger.error("Error in run_second_batch: %s", str(e), exc_info=True)
        # Update job status to failed
        job = Job.objects.get(job_id=job_id)
        job.status = 'FAILED'
        job.error = str(e)
        job.save()
        raise

@shared_task
def finalize_results(second_agg, job_id, first_agg):
    """Combines results from both batches into a final dictionary."""
    try:
        logger.info("Finalizing results - first_agg: %s, second_agg: %s", first_agg, second_agg)
        
        # Combine results
        final_result = {
            "first_batch": first_agg,
            "second_batch": second_agg
        }
        
        # Update job status and result
        job = Job.objects.get(job_id=job_id)
        job.status = 'COMPLETED'
        job.result = json.dumps(final_result)
        job.save()
        
        return final_result
    except Exception as e:
        logger.error("Error in finalize_results: %s", str(e), exc_info=True)
        # Update job status to failed
        job = Job.objects.get(job_id=job_id)
        job.status = 'FAILED'
        job.error = str(e)
        job.save()
        raise

@shared_task(bind=True)
def orchestrate_tasks(self, username, job_id):
    """Orchestrates the entire workflow."""
    try:
        # Update job status to running
        job = Job.objects.get(job_id=job_id)
        job.status = 'RUNNING'
        job.save()
        
        # Create first batch
        first_batch = group(run_task.s(f"{username}-b1-{i}") for i in range(5))
        
        # Create the workflow
        workflow = chain(
            chord(first_batch, aggregate.s(username=username)),
            create_second_batch.s(job_id=job_id),
            run_second_batch.s(job_id=job_id)
        )
        
        # Start the workflow
        workflow.apply_async()
        
    except Exception as e:
        # Update job status to failed
        job = Job.objects.get(job_id=job_id)
        job.status = 'FAILED'
        job.error = str(e)
        job.save()
        raise
