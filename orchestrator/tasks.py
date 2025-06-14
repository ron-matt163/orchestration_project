from celery import shared_task
import random
import time


@shared_task
def run_task(task_id, base_value=None):
    """Executes a task with random delay and returns a result, optionally adding a base value."""
    time.sleep(random.randint(1, 3))
    result = random.randint(100, 999)
    if base_value is not None:
        result += base_value
    print(f"Parallel Task {task_id} completed with result {result}")
    return {"task_id": task_id, "result": result}


@shared_task
def aggregate_results(task_outputs):
    """Aggregates the results of multiple tasks and returns a final result."""
    time.sleep(300)
    total = sum(item["result"] for item in task_outputs)
    print(f"Aggregation completed with total {total}")
    return {"aggregated_sum": total}
