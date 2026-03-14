# Resilient Decision System

A configurable, stateful workflow decision platform capable of evaluating incoming requests against variable rules arrays, executing workflow stages with deterministic outcome logging, preserving rigorous audit trails, and simulating retries resilience mechanisms.

## Project Deliverables Covered
- **Architecture design**: Refer to `ARCHITECTURE.md`
- **Configurability**: Workflows defined completely in `config/workflows.json` natively. New rule thresholds do not require code changes.
- **REST API + Swagger**: Available via standard FastAPI integration.
- **Explainability**: Provided through `DECISIONS.md`.
- **Testing**: In `/tests`. Uses Pytest to achieve robust coverage.

## Setup Instructions

**Prerequisites**: Python 3.9+ 

1. **Activate Virtual Environment** (If not already enabled):
```powershell
.\venv\Scripts\Activate.ps1
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the FastAPI server**:
```bash
uvicorn main:app --reload
```

## API Usage Reference

The default FastAPI implementation auto-generates Swagger documentation. After launching the server, visit:
**[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

### Key Endpoints

- `GET /config`:
  View the hot-loaded active configuration mapping, validating the business logic without opening code.

- `POST /requests`:
  Submit an intake request. Requires `workflow_id`, an `idempotency_key` (UUID), and a completely dynamic `payload`. 
  *Example body:*
  ```json
  {
    "workflow_id": "application_approval",
    "idempotency_key": "c7110ad2-1c25-4560-afaa-485dd479dfc8",
    "payload": {
      "applicant_name": "Alice Smith",
      "age": 32,
      "credit_score": 750
    }
  }
  ```

- `GET /requests/{request_id}`:
  Will retrieve the current execution flow state, the exact `current_stage`, the `retry_count`, and the granularly stored `audit_logs` history detailing every evaluated rule trace.

- `POST /requests/{request_id}/retry`:
  Retry a workflow that has landed in the `RETRY` or `MANUAL_REVIEW` status due to dependency failure.

## Executing Tests

To run the robust test suite tracking business correctness, payload parsing, duplicate detection idempotency, and resilience retry chains:

```console
pytest tests/ -v
```
