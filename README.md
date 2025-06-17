# Orchestration Challenge – Django + Celery + Docker

This Django-based orchestration service executes two distinct batches of parallel tasks, each followed by an aggregation task. It uses Django, Celery, Redis, and Docker Compose, with persistent job tracking in the database.

## Architecture

- **Django**: REST API endpoints for job orchestration and status tracking
- **Celery**: Task queue for parallel task execution and aggregation
- **Redis**: Message broker and result backend
- **SQLite**: Database for job tracking and status management

## Core Components

- `orchestrator/models.py`: Job model for tracking task status and results
- `orchestrator/tasks.py`: Celery tasks for task execution and orchestration
- `orchestrator/views.py`: REST endpoints for job management

## Prerequisites

- Docker 19+ and Docker Compose v2
- (Optional for local dev) Python 3.10 with `pip` / Poetry

## Steps

### 1️⃣ Clone & build

```bash
git clone <repo-url>
cd orchestration_project
docker compose build
```

### 2️⃣ Run the stack

```bash
docker compose up
```

- **web** – Django dev server on [http://localhost:8010](http://localhost:8010)
- **celery** – Celery worker connected to Redis
- **redis** – Broker / result backend

### 3️⃣ Use the API

1. Start a new job:

```bash
curl -X POST http://localhost:8010/orchestrate/<username>
```

Response:

```json
{
  "message": "Orchestration started.",
  "job_id": "<job_id>",
  "status_url": "/status/<username>/<job_id>"
}
```

2. Check job status:

```bash
curl http://localhost:8010/status/<username>/<job_id>
```

Response:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "COMPLETED",
  "created_at": "2025-06-17T18:00:01Z",
  "updated_at": "2025-06-17T18:06:01Z",
  "result": {
    "first_batch": { "aggregated_sum": 3149 },
    "second_batch": { "aggregated_sum": 5096 }
  }
}
```

## 🧩 How It Works

1. **Job Creation**: `POST /orchestrate/<username>` creates a new job and starts the workflow
2. **First Batch**: Executes 5 parallel tasks, each taking ~3 minutes
3. **First Aggregation**: Aggregates results from first batch (~3 minutes)
4. **Second Batch**: Uses first batch result to create 5 more parallel tasks
5. **Second Aggregation**: Aggregates results from second batch
6. **Finalization**: Combines both batch results and marks job as complete

## Features

- Persistent job tracking in database
- Status updates (PENDING, RUNNING, COMPLETED, FAILED)
- Maximum 3 concurrent jobs per user
- Non-blocking task execution with proper task chaining and result aggregation
