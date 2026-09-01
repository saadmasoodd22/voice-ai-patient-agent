import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "ok"
    assert res.json()["error"] is None


def test_list_patients_seeded(client):
    res = client.get("/patients")
    assert res.status_code == 200
    body = res.json()
    assert body["error"] is None
    assert len(body["data"]) >= 1


def test_create_validate_and_soft_delete(client):
    payload = {
        "first_name": "Test",
        "last_name": "Caller",
        "date_of_birth": "01/15/1990",
        "sex": "Female",
        "phone_number": "2025550109",
        "address_line_1": "100 Test Street",
        "city": "Washington",
        "state": "DC",
        "zip_code": "20001",
    }
    created = client.post("/patients", json=payload)
    assert created.status_code == 201
    patient_id = created.json()["data"]["patient_id"]

    bad = client.post("/patients", json={**payload, "date_of_birth": "01/15/2999", "phone_number": "2025550119"})
    assert bad.status_code == 422
    assert bad.json()["data"] is None

    listed = client.get("/patients", params={"last_name": "Caller", "phone_number": "2025550109"})
    assert listed.status_code == 200
    assert listed.json()["data"][0]["patient_id"] == patient_id

    deleted = client.delete(f"/patients/{patient_id}")
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted_at"] is not None

    hidden = client.get("/patients", params={"phone_number": "2025550109"})
    assert hidden.json()["data"] == []
