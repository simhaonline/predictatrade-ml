# tests/test_api_smoke.py

from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "OK"


def test_astro_now():
    r = client.get("/astro/now")
    assert r.status_code == 200
    data = r.json()
    assert "planets" in data
    assert "sessions" in data
    assert "fear_profile" in data


def test_reports_latest():
    r = client.get("/api/reports/latest")
    assert r.status_code == 200
    data = r.json()
    assert "date" in data
    assert "sessions" in data
    assert isinstance(data["sessions"], dict)
