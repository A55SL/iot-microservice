import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.database import Base, get_db, engine
from app.main import app
from fastapi.testclient import TestClient

Base.metadata.create_all(bind=engine)
client = TestClient(app)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_reading_no_alert():
    response = client.post("/sensors/readings", json={
        "device_id": "sensor-01",
        "value": 50.0,
        "unit": "celsius"
    })
    assert response.status_code == 201
    assert response.json()["alert"] is None


def test_reading_warning_alert():
    response = client.post("/sensors/readings", json={
        "device_id": "sensor-01",
        "value": 80.0,
        "unit": "celsius"
    })
    assert response.status_code == 201
    assert response.json()["alert"]["severity"] == "WARNING"


def test_reading_critical_alert():
    response = client.post("/sensors/readings", json={
        "device_id": "sensor-01",
        "value": 95.0,
        "unit": "celsius"
    })
    assert response.status_code == 201
    assert response.json()["alert"]["severity"] == "CRITICAL"


def test_get_readings():
    response = client.get("/sensors/readings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_alerts():
    response = client.get("/alerts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)