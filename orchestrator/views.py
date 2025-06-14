from rest_framework.decorators import api_view
from rest_framework.response import Response
from celery import group
from orchestrator.tasks import run_task, aggregate_results


@api_view(["POST"])
def orchestrate(request):
    """
    Executes two batches of parallel tasks with intermediate aggregation
    and returns all results.
    """
    # ---------- First batch of 5 parallel tasks ----------
    batch1_group = group(run_task.s(f"batch1-{i}") for i in range(5)).apply_async()
    batch1_results = batch1_group.get(timeout=300)        # <-- blocks until done

    # ---------- First aggregation task ----------
    aggregation1_task = aggregate_results.s(batch1_results).apply_async()
    aggregation1 = aggregation1_task.get(timeout=310)
    base_value = aggregation1["aggregated_sum"] // 5

    # ---------- Second batch of 5 parallel tasks ----------
    batch2_group = group(
        run_task.s(f"batch2-{i}", base_value=base_value) for i in range(5)
    ).apply_async()
    batch2_results = batch2_group.get(timeout=300)

    # ---------- Final aggregation ----------
    aggregation2_task = aggregate_results.s(batch2_results).apply_async()
    aggregation2 = aggregation2_task.get(timeout=310)

    return Response(
        {
            "batch1": batch1_results,
            "first_aggregation": aggregation1,
            "batch2": batch2_results,
            "second_aggregation": aggregation2,
        }
    )
