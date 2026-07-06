import sqlite3
import sys
from pathlib import Path

BUILTIN_CATEGORIES = [
    "spożywcze", "mieszkanie", "transport", "rachunki", "zdrowie",
    "rozrywka", "ubrania", "restauracje", "subskrypcje", "zwierzęta", "inne",
]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS categories(
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    builtin INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS transactions(
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('income','expense')),
    amount_grosze INTEGER NOT NULL,
    description TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id));
CREATE TABLE IF NOT EXISTS keyword_map(
    keyword TEXT PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(id));
CREATE TABLE IF NOT EXISTS settings(
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL);
"""


def data_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def connect(db_path=None) -> sqlite3.Connection:
    path = db_path or data_dir() / "biedaos.db"
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA)
    for name in BUILTIN_CATEGORIES:
        conn.execute("INSERT OR IGNORE INTO categories(name, builtin) VALUES(?, 1)", (name,))
    conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES('ollama_model', 'llama3.2:3b')")
    conn.commit()
    return conn
