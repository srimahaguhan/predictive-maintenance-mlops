import pytest
from fastapi.testclient import TestClient
from src.app import app  # This imports your FastAPI app logic

client = TestClient(app)

def test_read_health():
    """Verify the health endpoint returns 200 OK"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_read_ready():
    """Verify the ready endpoint is reachable"""
    response = client.get("/ready")
    assert response.status_code == 200

def test_prediction_logic():
    """Verify the prediction endpoint handles a valid payload"""
    payload = {
        "air_temp": 300.0,
        "process_temp": 310.0,
        "rotational_speed": 1500,
        "torque": 40.0,
        "tool_wear": 50,
        "client_id": "unit_test_runner"
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert "prediction" in response.json()