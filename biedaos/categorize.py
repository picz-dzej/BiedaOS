import http.client
import json
import re
import urllib.request

OLLAMA_URL = "http://127.0.0.1:11434"

BUILTIN_KEYWORDS = {
    "spożywcze": ["biedronka", "lidl", "żabka", "zabka", "auchan", "kaufland",
                  "carrefour", "dino", "aldi", "spożyw", "warzywniak",
                  "stokrotka", "netto", "polo market", "intermarche", "lewiatan",
                  "groszek", "delikatesy", "piekarnia", "rossmann", "hebe"],
    "transport": ["orlen", "paliwo", "benzyna", "mpk", "ztm", "pkp", "bilet",
                  "uber", "bolt", "parking", "autostrada",
                  "bp", "shell", "circle k", "moya", "amic", "lotos", "taxi"],
    "mieszkanie": ["czynsz", "wynajem", "mieszkanie"],
    "rachunki": ["prąd", "prad", "gaz", "woda", "internet", "telefon", "rachunek"],
    "zdrowie": ["apteka", "lekarz", "dentysta", "badania", "leki", "przychodnia"],
    "rozrywka": ["kino", "koncert", "steam", "gra", "książka", "ksiazka", "empik"],
    "ubrania": ["ubrania", "buty", "zara", "reserved", "sinsay", "cropp"],
    "restauracje": ["restauracja", "pizza", "kebab", "mcdonald", "kfc", "glovo",
                    "pyszne", "kawiarnia", "kawa na mieście"],
    "subskrypcje": ["netflix", "spotify", "youtube premium", "subskrypcja",
                    "abonament", "hbo", "disney", "icloud"],
    "zwierzęta": ["weterynarz", "karma", "zoolog", "psi fryzjer"],
}

_WORD_CHARS = "a-z0-9ąćęłńóśźż"


def _keyword_hit(norm: str, word: str) -> bool:
    # Krótkie słowa kluczowe (bp, gaz, gra…) tylko jako całe słowo — inaczej
    # "gazeta" wpadałaby w rachunki, a "herbpol" w transport.
    if len(word) <= 3:
        return re.search(rf"(?<![{_WORD_CHARS}]){re.escape(word)}(?![{_WORD_CHARS}])", norm) is not None
    return word in norm


def normalize(desc: str) -> str:
    return re.sub(r"\s+", " ", desc.lower()).strip()


def get_model(conn) -> str:
    row = conn.execute("SELECT value FROM settings WHERE key='ollama_model'").fetchone()
    return row["value"] if row else "llama3.2:3b"


def categorize(conn, description: str) -> int:
    norm = normalize(description)
    row = conn.execute("SELECT category_id FROM keyword_map WHERE keyword=?", (norm,)).fetchone()
    if row:
        return row["category_id"]
    cats = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM categories")}
    for cat_name, words in BUILTIN_KEYWORDS.items():
        if cat_name in cats and any(_keyword_hit(norm, w) for w in words):
            return cats[cat_name]
    answer = ollama_categorize(norm, list(cats.keys()), get_model(conn))
    if answer in cats:
        return cats[answer]
    return cats["inne"]


def learn(conn, description: str, category_id: int) -> None:
    conn.execute(
        "INSERT INTO keyword_map(keyword, category_id) VALUES(?, ?) "
        "ON CONFLICT(keyword) DO UPDATE SET category_id=excluded.category_id",
        (normalize(description), category_id),
    )
    conn.commit()


def ollama_available() -> bool:
    try:
        with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=1) as r:
            return r.status == 200
    except (OSError, http.client.HTTPException):
        return False


def ollama_categorize(desc: str, categories: list[str], model: str) -> str | None:
    prompt = (
        "Przypisz polski wydatek domowy do jednej kategorii.\n"
        "Przykłady:\n"
        '"stokrotka" -> spożywcze\n'
        '"bp" -> transport\n'
        '"netflix" -> subskrypcje\n'
        '"apteka gemini" -> zdrowie\n'
        '"czynsz" -> mieszkanie\n'
        f'Wydatek: "{desc}"\n'
        f"Dostępne kategorie: {', '.join(categories)}\n"
        "Odpowiedz wyłącznie nazwą jednej kategorii z listy, bez żadnych innych słów."
    )
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        OLLAMA_URL + "/api/generate", data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            answer = json.loads(r.read())["response"]
    except (OSError, http.client.HTTPException, KeyError, ValueError):
        return None
    answer = answer.strip().strip('"».').lower()
    return answer if answer in categories else None
