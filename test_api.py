"""Tests for AIVOA-QMS.

These run against an in-memory SQLite database so no MySQL server or Groq API
key is needed. Only the endpoints whose behaviour is deterministic are covered:
duplicate detection, the complaint status workflow, and request validation.

The extraction and risk-assessment paths call out to an LLM and are left to
manual testing.
"""

import os

# In-memory so tests never touch the filesystem. A file-backed SQLite database
# is held open by SQLAlchemy's pool, and Windows refuses to unlink an open file,
# which made fixture teardown fail. A shared in-memory database also gives each
# test a clean slate once the engine below is recreated per test.
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, ComplaintDB, get_db
from main import app


def override_get_db():
    """Swap the MySQL session for a fresh in-memory SQLite one per request."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client():
    """One in-memory database per test, shared by every request in that test.

    The engine is created once here rather than per request, otherwise a POST
    followed by a GET would see two different databases. StaticPool keeps the
    single in-memory connection alive across sessions.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def per_test_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = per_test_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides[get_db] = override_get_db
        engine.dispose()


def make_complaint(**overrides):
    """Build a save payload.

    POST /api/complaints reads from a nested "extracted" object rather than the
    top level, so the flat fields have to be nested to be stored.
    """
    extracted = {
        "complaintSource": "Pharmacy",
        "customerName": "Apollo Pharmacy",
        "productId": "PRD-99887",
        "issueCategory": "Packaging",
        "urgencyLevel": "High",
        "complaintDescription": "Safety seals broken on 15 bottles.",
        "batchNumber": "BATCH-A",
    }
    extracted.update(overrides)
    return {
        "extracted": extracted,
        "riskAssessment": {"riskLevel": "High", "summary": "Seal failure on a sterile pack."},
        "completenessData": {"is_complete": True, "missing_fields": []},
    }


class TestHealth:
    def test_app_boots(self, client):
        response = client.get("/docs")
        assert response.status_code == 200


class TestComplaintPersistence:
    def test_create_and_list(self, client):
        created = client.post("/api/complaints", json=make_complaint())
        assert created.status_code == 200

        listed = client.get("/api/complaints")
        assert listed.status_code == 200
        assert len(listed.json()) == 1
        assert listed.json()[0]["customerName"] == "Apollo Pharmacy"

    def test_list_is_empty_initially(self, client):
        response = client.get("/api/complaints")
        assert response.status_code == 200
        assert response.json() == []


class TestDuplicateDetection:
    def test_no_duplicate_on_empty_db(self, client):
        response = client.post(
            "/api/check-duplicate",
            json={"customerName": "Apollo Pharmacy", "productId": "PRD-99887"},
        )
        assert response.status_code == 200
        assert response.json()["duplicate_detected"] is False

    def test_detects_matching_customer_and_product(self, client):
        client.post("/api/complaints", json=make_complaint())

        response = client.post(
            "/api/check-duplicate",
            json={"customerName": "Apollo Pharmacy", "productId": "PRD-99887"},
        )
        body = response.json()
        assert body["duplicate_detected"] is True
        assert "possible_duplicate_id" in body
        assert "Apollo Pharmacy" in body["duplicate_reason"]

    def test_different_product_is_not_a_duplicate(self, client):
        client.post("/api/complaints", json=make_complaint())

        response = client.post(
            "/api/check-duplicate",
            json={"customerName": "Apollo Pharmacy", "productId": "PRD-00000"},
        )
        assert response.json()["duplicate_detected"] is False

    def test_different_customer_is_not_a_duplicate(self, client):
        client.post("/api/complaints", json=make_complaint())

        response = client.post(
            "/api/check-duplicate",
            json={"customerName": "City Care", "productId": "PRD-99887"},
        )
        assert response.json()["duplicate_detected"] is False

    def test_batch_number_narrows_the_match(self, client):
        client.post("/api/complaints", json=make_complaint(batchNumber="BATCH-A"))

        same_batch = client.post(
            "/api/check-duplicate",
            json={
                "customerName": "Apollo Pharmacy",
                "productId": "PRD-99887",
                "batchNumber": "BATCH-A",
            },
        )
        other_batch = client.post(
            "/api/check-duplicate",
            json={
                "customerName": "Apollo Pharmacy",
                "productId": "PRD-99887",
                "batchNumber": "BATCH-B",
            },
        )
        assert same_batch.json()["duplicate_detected"] is True
        assert other_batch.json()["duplicate_detected"] is False

    def test_missing_fields_rejected(self, client):
        response = client.post("/api/check-duplicate", json={"customerName": "Apollo"})
        assert response.status_code == 422


class TestStatusWorkflow:
    def test_valid_status_is_accepted(self, client):
        created = client.post("/api/complaints", json=make_complaint())
        complaint_id = created.json()["id"]

        response = client.patch(
            f"/api/complaints/{complaint_id}/status", json={"status": "QA_REVIEW"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "QA_REVIEW"

    def test_each_documented_status_is_allowed(self, client):
        created = client.post("/api/complaints", json=make_complaint())
        complaint_id = created.json()["id"]

        for status in ["UNDER_INVESTIGATION", "QA_REVIEW", "CLOSED", "OPEN"]:
            response = client.patch(
                f"/api/complaints/{complaint_id}/status", json={"status": status}
            )
            assert response.status_code == 200, f"{status} was rejected"
            assert response.json()["status"] == status

    def test_invalid_status_is_rejected(self, client):
        created = client.post("/api/complaints", json=make_complaint())
        complaint_id = created.json()["id"]

        response = client.patch(
            f"/api/complaints/{complaint_id}/status", json={"status": "BANANA"}
        )
        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]

    def test_unknown_complaint_returns_404(self, client):
        response = client.patch("/api/complaints/999999/status", json={"status": "CLOSED"})
        assert response.status_code == 404
        assert response.json()["detail"] == "Complaint not found"
