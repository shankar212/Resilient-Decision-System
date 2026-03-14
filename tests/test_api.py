import pytest
import uuid
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from db.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_decision_system.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_happy_path():
    payload = {
        "applicant_name": "Alice Smith",
        "age": 25,
        "credit_score": 700
    }
    
    response = client.post("/requests", json={
        "workflow_id": "application_approval",
        "idempotency_key": str(uuid.uuid4()),
        "payload": payload
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"

def test_invalid_input_reject():
    # Missing name -> fails mandatory check
    payload = {
        "applicant_name": "",
        "age": 25,
        "credit_score": 700
    }
    
    response = client.post("/requests", json={
        "workflow_id": "application_approval",
        "idempotency_key": str(uuid.uuid4()),
        "payload": payload
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REJECT"

def test_idempotency():
    payload = {"applicant_name": "Bob", "age": 30, "credit_score": 800}
    idem_key = str(uuid.uuid4())
    
    # First request
    resp1 = client.post("/requests", json={
        "workflow_id": "application_approval",
        "idempotency_key": idem_key,
        "payload": payload
    })
    data1 = resp1.json()
    req_id = data1["request_id"]
    
    # Duplicate request
    resp2 = client.post("/requests", json={
        "workflow_id": "application_approval",
        "idempotency_key": idem_key,
        "payload": payload
    })
    data2 = resp2.json()
    
    assert data1["request_id"] == data2["request_id"]
    assert data1["status"] == data2["status"]

def test_dependency_failure_and_retry():
    idem_key = str(uuid.uuid4())
    payload = {
        "applicant_name": "Charlie",
        "age": 22,
        "credit_score": 680,
        "force_dependency_failure": True
    }
    
    # Request gets retry status due to failure
    resp = client.post("/requests", json={
        "workflow_id": "application_approval",
        "idempotency_key": idem_key,
        "payload": payload
    })
    data = resp.json()
    assert data["status"] == "RETRY"
    req_id = data["request_id"]
    
    status_resp = client.get(f"/requests/{req_id}")
    assert status_resp.json()["retry_count"] == 1
    
    # Retry manual trigger
    retry_resp = client.post(f"/requests/{req_id}/retry")
    assert retry_resp.json()["status"] == "RETRY"  # Still failing because flag is true in payload
    
    status_resp_2 = client.get(f"/requests/{req_id}")
    assert status_resp_2.json()["retry_count"] == 2
