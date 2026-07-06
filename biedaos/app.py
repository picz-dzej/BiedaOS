import sys
from datetime import date as _date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import categorize, db, parsing, recommend


def static_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "biedaos" / "static"
    return Path(__file__).parent / "static"


def prev_month(month: str) -> str:
    y, m = int(month[:4]), int(month[5:7])
    y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return f"{y:04d}-{m:02d}"


class EntryIn(BaseModel):
    text: str
    type: str = "expense"
    date: str | None = None


class TxPatch(BaseModel):
    date: str | None = None
    description: str | None = None
    amount_grosze: int | None = None
    type: str | None = None
    category_id: int | None = None


class CategoryIn(BaseModel):
    name: str


class SettingsIn(BaseModel):
    ollama_model: str


def create_app(db_path=None) -> FastAPI:
    app = FastAPI(title="BiedaOS")
    conn = db.connect(db_path)

    def month_data(month: str):
        txs = [dict(r) for r in conn.execute(
            "SELECT t.id, t.date, t.type, t.amount_grosze, t.description, "
            "t.category_id, c.name AS category FROM transactions t "
            "LEFT JOIN categories c ON c.id = t.category_id "
            "WHERE substr(t.date, 1, 7) = ? ORDER BY t.date DESC, t.id DESC", (month,))]
        income = sum(t["amount_grosze"] for t in txs if t["type"] == "income")
        by_cat: dict[str, int] = {}
        for t in txs:
            if t["type"] == "expense":
                name = t["category"] or "inne"
                by_cat[name] = by_cat.get(name, 0) + t["amount_grosze"]
        return txs, income, by_cat

    @app.get("/api/months")
    def months():
        rows = conn.execute(
            "SELECT DISTINCT substr(date, 1, 7) AS m FROM transactions ORDER BY m").fetchall()
        return [r["m"] for r in rows]

    @app.get("/api/months/{month}")
    def month_summary(month: str):
        txs, income, by_cat = month_data(month)
        _, _, prev_by_cat = month_data(prev_month(month))
        last3, m = [], month
        for _ in range(3):
            _, i, bc = month_data(m)
            last3.append((i, sum(bc.values())))
            m = prev_month(m)
        last3.reverse()
        total = sum(by_cat.values())
        return {
            "month": month, "income": income, "expenses": total,
            "balance": income - total, "by_category": by_cat, "transactions": txs,
            "recommendations": recommend.recommendations(income, by_cat, prev_by_cat, last3),
        }

    @app.post("/api/transactions")
    def add_tx(entry: EntryIn):
        if entry.type not in ("income", "expense"):
            raise HTTPException(422, "Typ musi być income albo expense.")
        try:
            desc, grosze = parsing.parse_entry(entry.text)
        except parsing.ParseError as e:
            raise HTTPException(422, str(e))
        d = entry.date or _date.today().isoformat()
        cat_id = categorize.categorize(conn, desc) if entry.type == "expense" else None
        cur = conn.execute(
            "INSERT INTO transactions(date, type, amount_grosze, description, category_id) "
            "VALUES(?, ?, ?, ?, ?)", (d, entry.type, grosze, desc, cat_id))
        conn.commit()
        return {"id": cur.lastrowid}

    @app.patch("/api/transactions/{tx_id}")
    def patch_tx(tx_id: int, patch: TxPatch):
        row = conn.execute("SELECT * FROM transactions WHERE id=?", (tx_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Nie ma takiej transakcji.")
        fields = patch.model_dump(exclude_none=True)
        if not fields:
            return {"ok": True}
        if "type" in fields and fields["type"] not in ("income", "expense"):
            raise HTTPException(422, "Typ musi być income albo expense.")
        sets = ", ".join(f"{k}=?" for k in fields)
        conn.execute(f"UPDATE transactions SET {sets} WHERE id=?", (*fields.values(), tx_id))
        conn.commit()
        if "category_id" in fields:
            categorize.learn(conn, row["description"], fields["category_id"])
        return {"ok": True}

    @app.delete("/api/transactions/{tx_id}")
    def delete_tx(tx_id: int):
        conn.execute("DELETE FROM transactions WHERE id=?", (tx_id,))
        conn.commit()
        return {"ok": True}

    @app.get("/api/categories")
    def categories():
        return [dict(r) for r in conn.execute(
            "SELECT id, name, builtin FROM categories ORDER BY builtin DESC, name")]

    @app.post("/api/categories")
    def add_category(cat: CategoryIn):
        name = cat.name.strip().lower()
        if not name:
            raise HTTPException(422, "Pusta nazwa kategorii.")
        exists = conn.execute("SELECT 1 FROM categories WHERE name=?", (name,)).fetchone()
        if exists:
            raise HTTPException(409, "Taka kategoria już istnieje.")
        cur = conn.execute("INSERT INTO categories(name, builtin) VALUES(?, 0)", (name,))
        conn.commit()
        return {"id": cur.lastrowid}

    @app.get("/api/ollama/status")
    def ollama_status():
        return {"available": categorize.ollama_available(), "model": categorize.get_model(conn)}

    @app.get("/api/settings")
    def get_settings():
        return {"ollama_model": categorize.get_model(conn)}

    @app.put("/api/settings")
    def put_settings(s: SettingsIn):
        conn.execute(
            "INSERT INTO settings(key, value) VALUES('ollama_model', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (s.ollama_model.strip(),))
        conn.commit()
        return {"ok": True}

    @app.get("/api/trend")
    def trend():
        last = conn.execute("SELECT MAX(substr(date, 1, 7)) AS m FROM transactions").fetchone()["m"]
        month = max(last or "", _date.today().isoformat()[:7])
        out, m = [], month
        for _ in range(12):
            _, income, by_cat = month_data(m)
            out.append({"month": m, "income": income, "expenses": sum(by_cat.values())})
            m = prev_month(m)
        out.reverse()
        return out

    if static_dir().exists():
        app.mount("/", StaticFiles(directory=static_dir(), html=True), name="static")
    return app
