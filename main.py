from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from db.database import get_db, init_db
from schemas.api import WorkflowRunRequest, WorkflowRunResponse, WorkflowStatusResponse
from engine.workflow import run_workflow, retry_workflow, load_workflows
from models.domain import WorkflowRequest

app = FastAPI(title="Resilient Decision System", version="1.0.0")

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/requests", response_model=WorkflowRunResponse)
def create_request(request: WorkflowRunRequest, db: Session = Depends(get_db)):
    try:
        req_obj = run_workflow(
            db=db,
            workflow_id=request.workflow_id,
            idempotency_key=request.idempotency_key,
            payload=request.payload
        )
        return WorkflowRunResponse(
            request_id=req_obj.id,
            status=req_obj.state.status,
            current_stage=req_obj.state.current_stage,
            message="Workflow execution completed or paused."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/requests/{request_id}", response_model=WorkflowStatusResponse)
def get_request_status(request_id: str, db: Session = Depends(get_db)):
    req_obj = db.query(WorkflowRequest).filter_by(id=request_id).first()
    if not req_obj:
        raise HTTPException(status_code=404, detail="Request not found")
        
    return WorkflowStatusResponse(
        request_id=req_obj.id,
        status=req_obj.state.status,
        current_stage=req_obj.state.current_stage,
        retry_count=req_obj.state.retry_count,
        audit_logs=req_obj.audit_logs
    )

@app.post("/requests/{request_id}/retry", response_model=WorkflowRunResponse)
def retry_request(request_id: str, db: Session = Depends(get_db)):
    try:
        req_obj = retry_workflow(db=db, request_id=request_id)
        return WorkflowRunResponse(
            request_id=req_obj.id,
            status=req_obj.state.status,
            current_stage=req_obj.state.current_stage,
            message="Workflow retry execution completed or paused."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/config")
def get_config():
    return load_workflows()

