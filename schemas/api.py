from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class WorkflowRunRequest(BaseModel):
    workflow_id: str
    idempotency_key: str
    payload: Dict[str, Any]

class WorkflowRunResponse(BaseModel):
    request_id: str
    status: str
    current_stage: str
    message: str

class AuditLogSchema(BaseModel):
    stage: str
    action: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True

class WorkflowStatusResponse(BaseModel):
    request_id: str
    status: str
    current_stage: str
    retry_count: int
    audit_logs: List[AuditLogSchema]
    
    class Config:
        from_attributes = True
