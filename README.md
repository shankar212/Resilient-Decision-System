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

### Available Endpoints for Testing

You can use the Swagger UI (`/docs`), Postman, or `curl` to test the following endpoints.

#### 1. Check Root Connection
Ensure the API is responsive.
- **Endpoint**: `GET /`
- **Expected Response**: `{"message": "Welcome to the Resilient Decision System API..."}`

#### 2. View Active Configuration
View the currently loaded business rules mapping without opening code.
- **Endpoint**: `GET /config`

#### 3. Submit a New Request (Happy Path)
Triggers a new workflow evaluation.
- **Endpoint**: `POST /requests`
- **Body Example**:
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

#### 4. Trigger Dependency Failure (Retry Path)
Simulates a breakdown in background-checks by passing a flag.
- **Endpoint**: `POST /requests`
- **Body Example**:
  ```json
  {
    "workflow_id": "application_approval",
    "idempotency_key": "another-unique-uuid-here",
    "payload": {
      "applicant_name": "Charlie Flaky",
      "age": 30,
      "credit_score": 680,
      "force_dependency_failure": true
    }
  }
  ```
  *This will return a status of `RETRY`.*

#### 5. Check Request Status & Audit Trail
Check the exact state and read the full traceability ledger of a past execution.
- **Endpoint**: `GET /requests/{request_id}`
- **Note**: Replace `{request_id}` with the UUID returned from the Step 3/4 POST response.

#### 6. Manually Trigger a Retry
Forces the system to re-evaluate a workflow paused in `RETRY` or `MANUAL_REVIEW`.
- **Endpoint**: `POST /requests/{request_id}/retry`

## Executing Tests

To run the robust test suite tracking business correctness, payload parsing, duplicate detection idempotency, and resilience retry chains:

```console
pytest tests/ -v
```
