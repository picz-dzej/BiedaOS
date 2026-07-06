# BiedaOS — spec projektu (v1)

Data: 2026-07-06
Status: zatwierdzony przez Kubę

## Co to jest

Lokalny kalkulator finansowy. Użytkownik wpisuje przychody i wydatki w naturalnym języku
(`biedronka 47,30`), apka kategoryzuje, sumuje per miesiąc, rysuje wykresy i daje
regułowe rekomendacje. Działa w 100% offline, dane na dysku użytkownika.
Dystrybucja: jeden plik wykonywalny (Windows `.exe` + macOS), budowany przez GitHub Actions.

## Architektura

- **Backend:** Python 3.11+, FastAPI + uvicorn, SQLite (stdlib `sqlite3`).
- **Frontend:** jeden statyczny HTML + vanilla JS + Chart.js (vendorowany lokalnie, bez CDN).
- **Start:** uruchomienie binarki startuje serwer na `http://127.0.0.1:8137`
  (gdy port zajęty — kolejny wolny) i otwiera domyślną przeglądarkę.
- **LLM:** Ollama pod `http://127.0.0.1:11434` — **opcjonalna**. Apka w pełni działa bez niej.
- Zero kont, zero sieci poza localhostem.

### Struktura repo

```
BiedaOS/
├── biedaos/
│   ├── __main__.py        # start serwera + otwarcie przeglądarki
│   ├── app.py             # FastAPI: API + serwowanie statyków
│   ├── db.py              # SQLite: schemat, migracja, dostęp
│   ├── parsing.py         # parser wpisu: kwota + opis
│   ├── categorize.py      # słownik → nauczone korekty → Ollama
│   ├── recommend.py       # reguły rekomendacji
│   └── static/            # index.html, app.js, style.css, chart.umd.js
├── tests/
├── docs/superpowers/specs/
├── .github/workflows/build.yml
├── README.md              # po polsku, sekcja "opcjonalnie: Ollama"
└── pyproject.toml
```

## Dane

Plik `biedaos.db` w folderze obok binarki (przy uruchomieniu ze źródeł — katalog projektu).
Backup = skopiowanie pliku. Kwoty przechowywane w **groszach (INTEGER)** — bez błędów float.

Tabele:

- `transactions(id, date TEXT ISO, type TEXT 'income'|'expense', amount_grosze INTEGER, description TEXT, category_id INTEGER NULL dla income)`
- `categories(id, name TEXT UNIQUE, builtin INTEGER)` — startowe: spożywcze, mieszkanie,
  transport, rachunki, zdrowie, rozrywka, ubrania, restauracje, subskrypcje, zwierzęta, inne.
  Użytkownik może dodawać własne; builtin nieusuwalne.
- `keyword_map(keyword TEXT UNIQUE, category_id)` — nauczone korekty (patrz niżej).
- `settings(key TEXT UNIQUE, value TEXT)` — np. nazwa modelu Ollamy.

Miesiąc = pochodna `date` (`YYYY-MM`). Transakcje można edytować (data, kwota, opis,
kategoria, typ) i usuwać.

## Wpis i kategoryzacja

Jedno pole tekstowe + przełącznik wydatek/przychód (domyślnie wydatek).

**Parser (`parsing.py`):** kwota = ostatnia liczba w tekście (formaty: `47`, `47,30`, `47.30`,
`1 200`), opis = reszta. Brak liczby → błąd walidacji w UI. Data domyślnie dziś, edytowalna.

**Kategoryzacja (`categorize.py`) — kaskada:**
1. **Nauczone korekty:** znormalizowany opis (lowercase, bez kwoty) szukany w `keyword_map`.
2. **Słownik wbudowany:** mapowanie słów kluczowych (biedronka/lidl/żabka→spożywcze,
   orlen/paliwo/mpk→transport itd.).
3. **Ollama (jeśli dostępna):** prompt klasyfikacyjny z listą kategorii użytkownika,
   oczekiwana odpowiedź = dokładnie jedna nazwa kategorii; timeout 10 s; odpowiedź spoza
   listy lub błąd → krok 4.
4. **Fallback:** kategoria „inne".

Ręczna zmiana kategorii wpisu zapisuje znormalizowany opis do `keyword_map` —
apka uczy się bez LLM. Status Ollamy widoczny w UI jako dyskretny badge
(„AI: aktywne / offline — kategorie ze słownika").

Model domyślny: `llama3.2:3b`, zmienialny w ustawieniach.

## Widok miesięczny (UI)

Jedna strona:

- **Nagłówek:** `← lipiec 2026 →` — przełączanie miesięcy, pełna historia; miesiące
  z danymi dostępne z listy.
- **Podsumowanie:** przychody, wydatki, saldo (kolor: zielone/czerwone).
- **Wykresy:** donut — % przychodu zjadany przez każdą kategorię (+ segment „zostaje");
  słupki — wydatki vs przychody, ostatnie 12 miesięcy.
- **Rekomendacje:** lista komunikatów z reguł (niżej).
- **Lista transakcji miesiąca:** data, opis, kategoria (edytowalna inline), kwota, usuń.
- **Pole wpisu** zawsze na wierzchu — capture bez tarcia.

Język UI: polski. Waluta: PLN.

## Rekomendacje (`recommend.py`) — reguły, nie LLM

Deterministyczne, liczone dla wybranego miesiąca:

1. Kategoria > 25% przychodu → „X zjada N% przychodu".
2. Kategoria wzrosła m/m o >30% i >100 zł → „X skoczyło o N% względem poprzedniego miesiąca".
3. Saldo ujemne → „wydajesz więcej niż zarabiasz — to problem przychodu albo struktury, nie pojedynczych zakupów".
4. Wydatki > 90% przychodu (saldo dodatnie) → „zostaje mniej niż 10% bufora".
5. Suma trzech miesięcy: wydatki rosną szybciej niż przychody → sygnał trendu.
6. Brak przychodu w miesiącu przy istniejących wydatkach → przypomnienie o wpisaniu przychodu.

Brak spełnionych reguł → „wygląda zdrowo" + jedna liczba: stopa oszczędności.

## API (JSON, prefix `/api`)

- `GET /months` — lista miesięcy z danymi
- `GET /months/{YYYY-MM}` — podsumowanie: sumy, per kategoria, transakcje, rekomendacje
- `POST /transactions` — `{text, type, date?}` → parsowanie + kategoryzacja → zapis
- `PATCH /transactions/{id}` — edycja pól; zmiana kategorii uczy `keyword_map`
- `DELETE /transactions/{id}`
- `GET/POST /categories`
- `GET /ollama/status` — dostępność + nazwa modelu
- `GET/PUT /settings`

## Dystrybucja

- Repo na GitHubie. Workflow `build.yml`: na tag `v*` — PyInstaller `--onefile`
  na `windows-latest` i `macos-latest`, artefakty podpięte do GitHub Release.
- Znajomy: pobiera `BiedaOS.exe`, dwuklik (SmartScreen: „uruchom mimo to"), przeglądarka
  otwiera się sama. Bez Ollamy działa od razu.
- README: co to jest, jak uruchomić, gdzie są dane, jak zrobić backup, opcjonalna
  sekcja instalacji Ollamy (Windows i macOS) dla mądrzejszej kategoryzacji.

## Testy

pytest: parser (formaty kwot), kaskada kategoryzacji (bez Ollamy — mock), reguły
rekomendacji (przypadki brzegowe: brak przychodu, pierwszy miesiąc), smoke API (TestClient).

## Poza zakresem v1 (świadomie)

Multi-użytkownik, waluty ≠ PLN, import wyciągów bankowych, budżety/cele, aplikacja
mobilna, synchronizacja, rekomendacje z LLM, czat z danymi.
