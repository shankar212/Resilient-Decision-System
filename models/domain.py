import uuid
import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class WorkflowRequest(Base):
    __tablename__ = "requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String, nullable=False)
    idempotency_key = Column(String, unique=True, index=True, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    state = relationship("WorkflowState", back_populates="request", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="request")

class WorkflowState(Base):
    __tablename__ = "states"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String, ForeignKey("requests.id"), unique=True)
    current_stage = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING") # PENDING, SUCCESS, REJECTED, RETRY, MANUAL_REVIEW
    retry_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    request = relationship("WorkflowRequest", back_populates="state")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String, ForeignKey("requests.id"))
    stage = Column(String, nullable=False)
    action = Column(String, nullable=False) # e.g. RULE_EVALUATED, STAGE_TRANSITION, ERROR
    details = Column(JSON, nullable=True)   # e.g. rule condition matched, error message
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    request = relationship("WorkflowRequest", back_populates="audit_logs")
