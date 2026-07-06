import pytest
from fastapi.testclient import TestClient
from biedaos import categorize
from biedaos.app import create_app, prev_month


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(categorize, "ollama_categorize", lambda *a, **k: None)
    app = create_app(tmp_path / "t.db")
    return TestClient(app)


def test_prev_month():
    assert prev_month("2026-01") == "2025-12"
    assert prev_month("2026-07") == "2026-06"


def test_add_and_summarize(client):
    r = client.post("/api/transactions", json={"text": "biedronka 47,30", "type": "expense", "date": "2026-07-06"})
    assert r.status_code == 200
    client.post("/api/transactions", json={"text": "wypłata 5000", "type": "income", "date": "2026-07-01"})
    data = client.get("/api/months/2026-07").json()
    assert data["income"] == 500000
    assert data["expenses"] == 4730
    assert data["balance"] == 495270
    assert data["by_category"] == {"spożywcze": 4730}
    assert len(data["transactions"]) == 2
    assert isinstance(data["recommendations"], list)
    assert client.get("/api/months").json() == ["2026-07"]


def test_unparsable_entry_422(client):
    r = client.post("/api/transactions", json={"text": "same litery", "type": "expense"})
    assert r.status_code == 422


def test_patch_category_learns(client):
    tx = client.post("/api/transactions", json={"text": "dziwny sklep 10", "type": "expense", "date": "2026-07-06"}).json()
    cats = client.get("/api/categories").json()
    rozrywka = next(c["id"] for c in cats if c["name"] == "rozrywka")
    r = client.patch(f"/api/transactions/{tx['id']}", json={"category_id": rozrywka})
    assert r.status_code == 200
    tx2 = client.post("/api/transactions", json={"text": "dziwny sklep 20", "type": "expense", "date": "2026-07-06"}).json()
    data = client.get("/api/months/2026-07").json()
    t = next(t for t in data["transactions"] if t["id"] == tx2["id"])
    assert t["category"] == "rozrywka"


def test_patch_invalid_type_422(client):
    tx = client.post("/api/transactions", json={"text": "kino 30", "type": "expense", "date": "2026-07-06"}).json()
    r = client.patch(f"/api/transactions/{tx['id']}", json={"type": "foobar"})
    assert r.status_code == 422


def test_delete(client):
    tx = client.post("/api/transactions", json={"text": "kino 30", "type": "expense", "date": "2026-07-06"}).json()
    assert client.delete(f"/api/transactions/{tx['id']}").status_code == 200
    data = client.get("/api/months/2026-07").json()
    assert all(t["id"] != tx["id"] for t in data["transactions"])
