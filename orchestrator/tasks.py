import random
import time
import logging
from celery import shared_task, group, chord, chain

logger = logging.getLogger(__name__)

@shared_task
def run_task(task_id, base_value=None):
    time.sleep(random.randint(1, 3))
    n = random.randint(100, 999)
    if base_value is not None:
        n += base_value
    return {"task_id": task_id, "result": n}

@shared_task
def aggregate(batch_results):
    time.sleep(5 * 60)  # 5 minute sleep
    total = sum(x["result"] for x in batch_results)
    return {"aggregated_sum": total}

@shared_task
def create_second_batch(username, first_agg_result):
    """Creates the second batch of tasks with the base value from first aggregation."""
    base = first_agg_result["aggregated_sum"] // 5
    second_batch = group(run_task.s(f"{username}-b2-{i}", base) for i in range(5))
    return second_batch

@shared_task
def finalize_results(results):
    """Combines all results into the final format."""
    first_batch_results, first_agg_result, second_batch_results, second_agg_result = results
    result = {
        "batch1": first_batch_results,
        "first_aggregation": first_agg_result,
        "batch2": second_batch_results,
        "second_aggregation": second_agg_result
    }
    logger.info("Finalizing results: %s", result)
    return result

@shared_task(bind=True)
def orchestrate_tasks(self, username):
    """Orchestrates the entire workflow."""
    # Create first batch
    first_batch = group(run_task.s(f"{username}-b1-{i}") for i in range(5))
    
    # Create the workflow
    workflow = chain(
        chord(first_batch, aggregate.s()),
        create_second_batch.s(username),
        aggregate.s(),
        finalize_results.s()
    )
    
    # Start the workflow
    result = workflow.apply_async()
    return result.id
