import pytest
from biedaos import categorize, db


@pytest.fixture
def conn(tmp_path):
    return db.connect(tmp_path / "t.db")


def cat_id(conn, name):
    return conn.execute("SELECT id FROM categories WHERE name=?", (name,)).fetchone()["id"]


def test_builtin_keyword_match(conn, monkeypatch):
    monkeypatch.setattr(categorize, "ollama_categorize", lambda *a, **k: pytest.fail("nie wolno wołać Ollamy"))
    assert categorize.categorize(conn, "Biedronka") == cat_id(conn, "spożywcze")
    assert categorize.categorize(conn, "paliwo orlen") == cat_id(conn, "transport")


def test_learned_correction_beats_builtin(conn, monkeypatch):
    monkeypatch.setattr(categorize, "ollama_categorize", lambda *a, **k: None)
    categorize.learn(conn, "Biedronka", cat_id(conn, "rozrywka"))
    assert categorize.categorize(conn, "biedronka") == cat_id(conn, "rozrywka")


def test_ollama_used_when_no_match(conn, monkeypatch):
    monkeypatch.setattr(categorize, "ollama_categorize", lambda desc, cats, model: "zdrowie")
    assert categorize.categorize(conn, "wizyta u pana Zenka") == cat_id(conn, "zdrowie")


def test_fallback_inne(conn, monkeypatch):
    monkeypatch.setattr(categorize, "ollama_categorize", lambda *a, **k: None)
    assert categorize.categorize(conn, "coś dziwnego") == cat_id(conn, "inne")


def test_ollama_answer_outside_list_ignored(conn, monkeypatch):
    monkeypatch.setattr(categorize, "ollama_categorize", lambda *a, **k: None)
    assert categorize.categorize(conn, "xyz") == cat_id(conn, "inne")


def test_ollama_http_exception_swallowed(monkeypatch):
    import http.client

    def boom(*a, **k):
        raise http.client.IncompleteRead(b"")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    assert categorize.ollama_categorize("x", ["inne"], "llama3.2:3b") is None
    assert categorize.ollama_available() is False
