import pytest
from fastapi.testclient import TestClient
from biedaos import categorize
from biedaos.app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(categorize, "ollama_categorize", lambda *a, **k: None)
    monkeypatch.setattr(categorize, "ollama_available", lambda: False)
    return TestClient(create_app(tmp_path / "t.db"))


def test_add_category(client):
    r = client.post("/api/categories", json={"name": "hazard"})
    assert r.status_code == 200
    names = [c["name"] for c in client.get("/api/categories").json()]
    assert "hazard" in names
    assert client.post("/api/categories", json={"name": "hazard"}).status_code == 409


def test_ollama_status(client):
    assert client.get("/api/ollama/status").json() == {"available": False, "model": "llama3.2:3b"}


def test_settings_roundtrip(client):
    assert client.get("/api/settings").json() == {"ollama_model": "llama3.2:3b"}
    r = client.put("/api/settings", json={"ollama_model": "qwen2.5:3b"})
    assert r.status_code == 200
    assert client.get("/api/settings").json() == {"ollama_model": "qwen2.5:3b"}


def test_trend_12_months(client):
    client.post("/api/transactions", json={"text": "wypłata 5000", "type": "income", "date": "2026-07-01"})
    trend = client.get("/api/trend").json()
    assert len(trend) == 12
    july = next(t for t in trend if t["month"] == "2026-07")
    assert july["income"] == 500000
