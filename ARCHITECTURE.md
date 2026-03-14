# Architecture: Resilient Decision System

## System Design and Components

The Resilient Decision System is designed as a generic, configuration-driven decisioning engine. Its architecture revolves around decoupling business workflow definitions from core evaluation logic.

### 1. The Core Engine (`engine/workflow.py` & `engine/rules.py`)
- **Rules Evaluator**: A stateless processor evaluating logical conditions (thresholds, equality, presence) against a given payload.
- **Workflow Orchestrator**: Manages state transitions across multiple stages. It interprets the JSON configuration (e.g., `application_approval`) to decide whether to advance to the next state, reject, or halt for manual review based on rule outputs.

### 2. State & Database Layer (`db/database.py` & `models/domain.py`)
- Built on SQLAlchemy ORM (using SQLite for this implementation).
- **`WorkflowRequest`**: Stores incoming payload and the `idempotency_key`. 
- **`WorkflowState`**: Tracks the workflow’s progress (`current_stage`, `status`, `retry_count`). Crucial for resuming paused/failed operations.
- **`AuditLog`**: An append-only ledger that records every evaluated rule, state transition, and dependency error, providing 100% trace explainability.

### 3. API Layer (`main.py` & `schemas/api.py`)
- A FastAPI application exposing RESTful routes.
- Schema validation enforces payload structure natively via Pydantic bounds before reaching the workflow engine.

### 4. Dependency Simulator (`dependencies/external.py`)
- Mock integration simulating flaky external APIs. When a simulated exception rises, the engine halts, bumps a retry counter, and preserves the retry state.

## Data Flow
1. POST `/requests` intake. Pydantic validates payload constraints.
2. The orchestrator queries `idempotency_key`. If matched, returns the existing process.
3. If new, initial State and Request records are committed.
4. The system loops over the `stages` defined in `config/workflows.json`.
5. For each rule in a stage, it invokes `rules.py`. Every outcome emits an `AuditLog` row.
6. A terminal state (SUCCESS/REJECT/MANUAL_REVIEW) ends the processing. A generic exception (simulated network failure) triggers a RETRY state.

## Trade-offs and Assumptions
- **Synchronous vs. Asynchronous Compute**: To simplify deployment for this demonstration, the workflow engine computes synchronously during the HTTP request cycle. In higher-load production deployments, the worker execution should ideally be pushed onto an async queue (e.g. Celery / RabbitMQ), while API endpoints submit jobs and poll.
- **SQLite over Postgres**: Used for portability in this exercise. In production, concurrency locking row-level semantics (like `SELECT FOR UPDATE`) on Postgres is critical for strict idempotency at high scale. 
- **Configuration Hot-Reloading**: The application loads the configuration JSON dynamically per request, which satisfies the requirement to allow "changing requirements without major rewrites." 

## Scaling Considerations
- Horizontal scaling entails running multiple FastAPI workers behind a load balancer. 
- A persistent datastore (PostgreSQL instead of SQLite) alongside distributed caching (Redis) for fast `idempotency_key` checking is required at scale.
