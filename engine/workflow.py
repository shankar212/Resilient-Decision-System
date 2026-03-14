import json
import os
from sqlalchemy.orm import Session
from models.domain import WorkflowRequest, WorkflowState, AuditLog
from engine.rules import evaluate_stage_rules
from dependencies.external import call_external_dependency, ExternalDependencyError

def load_workflows():
    path = os.path.join(os.path.dirname(__file__), "..", "config", "workflows.json")
    with open(path, "r") as f:
        return json.load(f)

def run_workflow(db: Session, workflow_id: str, idempotency_key: str, payload: dict):
    # Idempotency check
    existing_req = db.query(WorkflowRequest).filter_by(idempotency_key=idempotency_key).first()
    if existing_req:
        return existing_req

    workflows = load_workflows()
    if workflow_id not in workflows:
        raise ValueError(f"Workflow {workflow_id} not found in configuration")

    workflow_def = workflows[workflow_id]
    
    # Init state
    req = WorkflowRequest(workflow_id=workflow_id, idempotency_key=idempotency_key, payload=payload)
    db.add(req)
    db.commit()
    db.refresh(req)
    
    initial_stage = workflow_def["stages"][0]["id"]
    state = WorkflowState(request_id=req.id, current_stage=initial_stage, status="PENDING")
    db.add(state)
    db.commit()
    db.refresh(state)

    audit_log = AuditLog(request_id=req.id, stage="INIT", action="WORKFLOW_STARTED", details={"workflow_id": workflow_id})
    db.add(audit_log)
    db.commit()

    return execute_stages(db, req, workflow_def)

def execute_stages(db: Session, req: WorkflowRequest, workflow_def: dict):
    state = req.state
    stages_map = {s["id"]: s for s in workflow_def["stages"]}
    
    while state.status == "PENDING" or state.status == "RETRY":
        current_stage_def = stages_map.get(state.current_stage)
        if not current_stage_def:
            state.status = "REJECTED"
            add_audit(db, req.id, state.current_stage, "ERROR", {"msg": "Stage not found"})
            break
            
        stage_type = current_stage_def.get("action", "evaluation")
        
        if stage_type == "evaluation":
            rules = current_stage_def.get("rules", [])
            success, failed_rule = evaluate_stage_rules(rules, req.payload)
            
            if success:
                add_audit(db, req.id, state.current_stage, "STAGE_PASSED", {"rules_evaluated": len(rules)})
                next_stage = current_stage_def.get("on_success")
                if next_stage in ["success", "reject", "manual_review"]:
                    state.status = next_stage.upper()
                else:
                    state.current_stage = next_stage
            else:
                add_audit(db, req.id, state.current_stage, "RULE_FAILED", {"failed_rule_id": failed_rule.get("id")})
                on_fail = failed_rule.get("on_fail", "reject")
                if on_fail in ["success", "reject", "manual_review"]:
                    state.status = on_fail.upper()
                else:
                    state.current_stage = on_fail
                    
        elif stage_type == "external_dependency":
            target = current_stage_def.get("mock_dependency_target")
            try:
                success = call_external_dependency(target, req.payload)
                if success:
                    add_audit(db, req.id, state.current_stage, "DEPENDENCY_SUCCESS", {"target": target})
                    next_stage = current_stage_def.get("on_success")
                    if next_stage in ["success", "reject", "manual_review"]:
                        state.status = next_stage.upper()
                    else:
                        state.current_stage = next_stage
                else:
                    add_audit(db, req.id, state.current_stage, "DEPENDENCY_FAILED", {"target": target})
                    on_fail = current_stage_def.get("on_fail", "reject")
                    if on_fail in ["success", "reject", "manual_review"]:
                        state.status = on_fail.upper()
                    else:
                        state.current_stage = on_fail
            except ExternalDependencyError as e:
                add_audit(db, req.id, state.current_stage, "DEPENDENCY_ERROR", {"error": str(e)})
                # Ensure retry_count is numeric
                current_retry = state.retry_count or 0
                state.retry_count = current_retry + 1
                limit = current_stage_def.get("retry_limit", 3)
                if state.retry_count > limit:
                    state.status = "MANUAL_REVIEW"
                    add_audit(db, req.id, state.current_stage, "RETRY_LIMIT_EXCEEDED", {"retry_count": state.retry_count})
                else:
                    state.status = "RETRY"
                db.commit()
                db.refresh(state)
                break # Break out to pause execution, allowing manual or cron retry later

        db.commit()
        db.refresh(state)
        
    return req

def add_audit(db: Session, request_id: str, stage: str, action: str, details: dict):
    audit = AuditLog(request_id=request_id, stage=stage, action=action, details=details)
    db.add(audit)
    db.commit()

def retry_workflow(db: Session, request_id: str):
    req = db.query(WorkflowRequest).filter_by(id=request_id).first()
    if not req:
        raise ValueError("Request not found")
        
    state = req.state
    if state.status not in ["RETRY", "MANUAL_REVIEW"]:
        raise ValueError(f"Request is in state {state.status}, cannot retry")
        
    state.status = "PENDING"
    add_audit(db, req.id, state.current_stage, "MANUAL_RETRY_TRIGGERED", {"previous_status": state.status})
    db.commit()
    
    workflows = load_workflows()
    return execute_stages(db, req, workflows[req.workflow_id])
