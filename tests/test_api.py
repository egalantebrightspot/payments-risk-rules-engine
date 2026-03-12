import pytest
from fastapi.testclient import TestClient

from risk_engine.api import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ── Health endpoint ─────────────────────────────────────────────


def test_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ── Scoring endpoint — happy path ──────────────────────────────


class TestScoreEndpoint:
    def test_low_risk(self, client: TestClient):
        payload = {
            "transaction_id": "T-API-LOW",
            "account_id": "A1",
            "amount": 50.0,
            "merchant_country": "US",
            "account_home_country": "US",
        }
        resp = client.post("/score", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["risk_tier"] == "low"
        assert body["rule_hits"] == []
        assert body["risk_score"] == 0.0

    def test_high_risk(self, client: TestClient):
        payload = {
            "transaction_id": "T-API-HIGH",
            "account_id": "A1",
            "amount": 950.0,
            "merchant_country": "BR",
            "account_home_country": "US",
        }
        resp = client.post("/score", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "HIGH_AMOUNT" in body["rule_hits"]
        assert "GEO_MISMATCH" in body["rule_hits"]
        assert body["risk_score"] == 0.45

    def test_block_tier(self, client: TestClient):
        payload = {
            "transaction_id": "T-API-BLOCK",
            "account_id": "A1",
            "amount": 5000.0,
            "merchant_country": "NG",
            "account_home_country": "US",
            "merchant_category": "gambling",
            "device_id": "DEV-NEW",
            "hour_of_day": 2,
            "recent_transaction_count": 10,
            "known_device": False,
        }
        resp = client.post("/score", json=payload)
        body = resp.json()
        assert body["risk_tier"] == "block"
        assert body["risk_score"] == 1.0
        assert len(body["rule_hits"]) == 6

    def test_minimal_payload_uses_defaults(self, client: TestClient):
        payload = {
            "transaction_id": "T-API-MIN",
            "account_id": "A1",
            "amount": 50.0,
        }
        resp = client.post("/score", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["transaction_id"] == "T-API-MIN"
        assert body["risk_tier"] == "low"


# ── Response schema ─────────────────────────────────────────────


class TestResponseSchema:
    def test_response_has_all_fields(self, client: TestClient):
        payload = {
            "transaction_id": "T-API-SCHEMA",
            "account_id": "A1",
            "amount": 600.0,
        }
        resp = client.post("/score", json=payload)
        body = resp.json()
        assert "transaction_id" in body
        assert "risk_score" in body
        assert "risk_tier" in body
        assert "rule_hits" in body
        assert "explanations" in body

    def test_risk_score_is_numeric(self, client: TestClient):
        payload = {
            "transaction_id": "T-API-NUM",
            "account_id": "A1",
            "amount": 600.0,
        }
        resp = client.post("/score", json=payload)
        body = resp.json()
        assert isinstance(body["risk_score"], (int, float))
        assert 0.0 <= body["risk_score"] <= 1.0

    def test_risk_tier_is_valid(self, client: TestClient):
        payload = {
            "transaction_id": "T-API-TIER",
            "account_id": "A1",
            "amount": 600.0,
        }
        resp = client.post("/score", json=payload)
        body = resp.json()
        assert body["risk_tier"] in ("low", "medium", "high", "block")

    def test_rule_hits_are_strings(self, client: TestClient):
        payload = {
            "transaction_id": "T-API-HITS",
            "account_id": "A1",
            "amount": 950.0,
            "merchant_country": "BR",
            "account_home_country": "US",
        }
        resp = client.post("/score", json=payload)
        body = resp.json()
        assert all(isinstance(h, str) for h in body["rule_hits"])

    def test_explanations_are_strings(self, client: TestClient):
        payload = {
            "transaction_id": "T-API-EXPL",
            "account_id": "A1",
            "amount": 950.0,
            "merchant_country": "BR",
            "account_home_country": "US",
        }
        resp = client.post("/score", json=payload)
        body = resp.json()
        assert all(isinstance(e, str) for e in body["explanations"])

    def test_explanations_contain_threshold_values(self, client: TestClient):
        payload = {
            "transaction_id": "T-API-THR",
            "account_id": "A1",
            "amount": 600.0,
            "merchant_country": "US",
            "account_home_country": "US",
        }
        resp = client.post("/score", json=payload)
        body = resp.json()
        assert any("600.00" in e for e in body["explanations"])


# ── Validation & error handling ─────────────────────────────────


class TestValidation:
    def test_missing_required_fields(self, client: TestClient):
        resp = client.post("/score", json={"amount": 100.0})
        assert resp.status_code == 422

    def test_missing_transaction_id(self, client: TestClient):
        payload = {"account_id": "A1", "amount": 100.0}
        resp = client.post("/score", json=payload)
        assert resp.status_code == 422

    def test_missing_account_id(self, client: TestClient):
        payload = {"transaction_id": "T1", "amount": 100.0}
        resp = client.post("/score", json=payload)
        assert resp.status_code == 422

    def test_empty_body(self, client: TestClient):
        resp = client.post("/score", json={})
        assert resp.status_code == 422

    def test_invalid_content_type(self, client: TestClient):
        resp = client.post("/score", content="not json")
        assert resp.status_code == 422

    def test_wrong_http_method_on_score(self, client: TestClient):
        resp = client.get("/score")
        assert resp.status_code == 405

    def test_nonexistent_endpoint(self, client: TestClient):
        resp = client.get("/does-not-exist")
        assert resp.status_code == 404
