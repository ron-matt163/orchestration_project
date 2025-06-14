# Orchestration Challenge – Django + Celery + Docker

This Django-based orchestration service executes two distinct batches of parallel tasks, each followed by an aggregation task (one after the other). It is built using Django, Celery, Redis, and Docker Compose.

The core logic can be found in `orchestrator/tasks.py` and `orchestrator/views.py`

## Prerequisites

- Docker 19+ and Docker Compose v2
- (Optional for local dev) Python 3.10 with `pip` / Poetry

## Steps

### 1️⃣ Clone & build

```bash
git clone <repo‑url>
cd orchestration_project
docker compose build
```

### 2️⃣ Run the stack

```bash
docker compose up
```

- **web** – Django dev server on [http://localhost:8010](http://localhost:8010)
- **celery** – Celery worker connected to Redis
- **redis** – Broker / result backend

### 3️⃣ Hit the endpoint

```bash
curl -X POST http://localhost:8010/orchestrate/ | jq
```

Example JSON response:

```json
{
  "batch1": [ {"task_id":"batch1-0","result":812}, ...],
  "first_aggregation": {"aggregated_sum": 4033},
  "batch2": [ {"task_id":"batch2-0","result":1675}, ...],
  "second_aggregation": {"aggregated_sum": 8123}
}
```

## 🧩 How It Works

1. **`POST /orchestrate/`** triggers the orchestration view.
2. The view submits **group A** of 5 `run_task` jobs via Celery and waits for completion (`GroupResult.get(timeout=…)`).
3. A single `aggregate_results` job receives the 5 outputs, sleeps (simulate heavy work), then returns a sum.
4. The sum influences **group B** (second 5 tasks). Another aggregation follows.
5. The view returns the complete payload.
