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


def test_settings_empty_model_422(client):
    assert client.put("/api/settings", json={"ollama_model": "  "}).status_code == 422


def test_concurrent_requests_no_error(client):
    # Regresja: frontend odpala 3 żądania naraz (Promise.all); współdzielone
    # połączenie SQLite dawało InterfaceError z cache'u statementów.
    import threading

    client.post("/api/transactions", json={"text": "wypłata 5000", "type": "income", "date": "2026-07-01"})
    errors = []

    def hammer():
        try:
            for _ in range(15):
                for path in ("/api/trend", "/api/months/2026-07", "/api/categories"):
                    r = client.get(path)
                    if r.status_code != 200:
                        errors.append((path, r.status_code))
        except Exception as e:  # noqa: BLE001 — każdy wyjątek wątku to fail testu
            errors.append(repr(e))

    threads = [threading.Thread(target=hammer) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []


def test_trend_12_months(client):
    client.post("/api/transactions", json={"text": "wypłata 5000", "type": "income", "date": "2026-07-01"})
    trend = client.get("/api/trend").json()
    assert len(trend) == 12
    july = next(t for t in trend if t["month"] == "2026-07")
    assert july["income"] == 500000
