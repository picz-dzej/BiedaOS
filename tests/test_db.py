from biedaos import db


def test_connect_creates_schema_and_seeds(tmp_path):
    conn = db.connect(tmp_path / "test.db")
    names = [r["name"] for r in conn.execute("SELECT name FROM categories ORDER BY id")]
    assert names == db.BUILTIN_CATEGORIES
    assert len(names) == 11
    model = conn.execute("SELECT value FROM settings WHERE key='ollama_model'").fetchone()
    assert model["value"] == "llama3.2:3b"


def test_connect_is_idempotent(tmp_path):
    path = tmp_path / "test.db"
    db.connect(path).close()
    conn = db.connect(path)
    count = conn.execute("SELECT COUNT(*) c FROM categories").fetchone()["c"]
    assert count == 11
