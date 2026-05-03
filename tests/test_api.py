import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.database import Base, engine
from app.main import app
from fastapi.testclient import TestClient

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)

from app.config import settings
HEADERS = {"X-API-Key": settings.API_KEY}

NORMAL_READING = {
    "turbine_id": "VES-V90-001",
    "timestamp": "2026-05-03T12:00:00Z",
    "wind_speed_m_s": 10.0,
    "rotor_rpm": 12.0,
    "power_output_kw": 1400.0,
    "blade_pitch_deg": 0.0,
    "nacelle_yaw_deg": 270.0,
    "generator_temp_c": 45.0,
    "gearbox_temp_c": 35.0,
    "main_bearing_temp_c": 28.0,
    "nacelle_temp_c": 20.0,
    "ambient_temp_c": 10.0,
    "main_bearing_vibration_mm_s": 1.2,
    "tower_vibration_mm_s": 0.7,
    "oil_pressure_bar": 4.5,
    "grid_frequency_hz": 50.0,
}


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_no_api_key_returns_401():
    response = client.post("/api/turbines/data", json=NORMAL_READING)
    assert response.status_code == 401


def test_receive_normal_reading():
    response = client.post("/api/turbines/data", json=NORMAL_READING, headers=HEADERS)
    assert response.status_code == 201
    assert response.json()["alerts_triggered"] == 0


def test_receive_overheating_reading():
    hot_reading = NORMAL_READING.copy()
    hot_reading["generator_temp_c"] = 95.0
    response = client.post("/api/turbines/data", json=hot_reading, headers=HEADERS)
    assert response.status_code == 201
    assert response.json()["alerts_triggered"] > 0


def test_low_oil_pressure_alert():
    low_oil = NORMAL_READING.copy()
    low_oil["oil_pressure_bar"] = 2.0
    response = client.post("/api/turbines/data", json=low_oil, headers=HEADERS)
    assert response.status_code == 201
    assert response.json()["alerts_triggered"] > 0


def test_get_readings():
    response = client.get("/api/turbines/readings", headers=HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_alerts():
    response = client.get("/api/alerts", headers=HEADERS)
    assert response.status_code == 200
    assert len(response.json()) > 0