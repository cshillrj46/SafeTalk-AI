import os

import pytest

os.environ.setdefault("API_KEYS_RAW", "test-key:cliente_teste")
os.environ.setdefault("AUDIT_DB_PATH", "test_audit_log.db")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

HEADERS = {"X-API-Key": "test-key"}


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint_is_public(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_without_api_key_is_rejected(client):
    response = client.post("/v1/analyze", json={"message": "qualquer coisa"})
    assert response.status_code in (401, 422)


def test_analyze_with_invalid_api_key_is_rejected(client):
    response = client.post(
        "/v1/analyze", json={"message": "qualquer coisa"}, headers={"X-API-Key": "chave-errada"}
    )
    assert response.status_code == 401


def test_analyze_obvious_scam_message_returns_high_risk(client):
    payload = {"message": "Pix urgente agora, troquei de número, é urgente, manda hoje!"}
    response = client.post("/v1/analyze", json=payload, headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["risk"] == "alto"
    assert body["source"] in {"regras", "ml", "llm"}
    assert "request_id" in body


def test_analyze_response_matches_schema_contract(client):
    payload = {"message": "Mensagem qualquer para teste de contrato de resposta."}
    response = client.post("/v1/analyze", json=payload, headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    for field in ["request_id", "risk", "confidence", "reason", "triggered_rules", "source"]:
        assert field in body


def test_stats_summary_endpoint_requires_auth(client):
    response = client.get("/v1/stats/summary")
    assert response.status_code in (401, 422)


def teardown_module() -> None:
    db_path = os.environ.get("AUDIT_DB_PATH", "test_audit_log.db")
    if os.path.exists(db_path):
        os.remove(db_path)
