# BiedaOS

Lokalny kalkulator finansowy. Twoje dane nie opuszczają Twojego komputera.

---

## Jak uruchomić (Windows)

1. Pobierz `BiedaOS.exe` z zakładki **Releases** na tej stronie.
2. Kliknij dwa razy. Windows może pokazać ostrzeżenie „nieznany wydawca" —
   kliknij „Więcej informacji" → „Uruchom mimo to".
3. Otworzy się czarne okienko, a po chwili przeglądarka z aplikacją.
   Czarne okienko zostaw otwarte — jego zamknięcie wyłącza aplikację.

---

## Jak uruchomić (Mac)

1. Pobierz `BiedaOS-mac` z zakładki **Releases**. `BiedaOS-mac` wymaga Maca z Apple Silicon (M1 lub nowszy).
2. Kliknij dwa razy. Jeśli Mac zablokuje plik (komunikat o nieznanym deweloperze),
   otwórz Terminal i wpisz:
   ```
   xattr -d com.apple.quarantine BiedaOS-mac
   chmod +x BiedaOS-mac
   ```
   Następnie uruchom plik ponownie.
3. W oknie terminala pojawi się adres `http://127.0.0.1:<port>` — przeglądarka
   otworzy się automatycznie. Zamknięcie okna terminala wyłącza aplikację.

---

## Jak używać

**Dodawanie wpisu:** wpisz opis i kwotę w jedno pole, np. `biedronka 47,30`.
Kwota to ostatnia liczba; akceptowane formaty: `47`, `47,30`, `47.30`, `1 200`, opcjonalnie z `zł`.
Datę możesz zmienić — domyślnie ustawia się na dzisiaj.
Jeśli wpis to przychód (pensja, zlecenie), przełącz przełącznik „przychód".

**Kategorie:** aplikacja ma 11 wbudowanych kategorii po polsku (spożywcze, mieszkanie,
transport, rachunki, zdrowie, rozrywka, ubrania, restauracje, subskrypcje, zwierzęta, inne).
Jeśli przypisana kategoria jest błędna, popraw ją w tabeli — następnym razem
to samo słowo kluczowe trafi od razu do właściwej kategorii. Własne kategorie
możesz dodać w stopce aplikacji.

**Nawigacja:** strzałki przy nagłówku miesiąca przełączają między miesiącami.

**Wykresy:** wykres pierścieniowy pokazuje, jaki procent przychodów pochłania każda kategoria
i ile zostaje. Widok roczny pokazuje wydatki miesiąc po miesiącu przez ostatnie 12 miesięcy.
Na podstawie danych aplikacja wyświetla też krótkie wskazówki.

---

## Twoje dane

Wszystko jest zapisane w pliku `biedaos.db` obok pliku aplikacji.
Backup to dosłownie skopiowanie tego jednego pliku w bezpieczne miejsce.

---

## Opcjonalnie: mądrzejsze kategorie (Ollama)

Bez żadnych dodatków aplikacja przypisuje kategorie na podstawie słownika słów kluczowych
i Twoich wcześniejszych korekt — wystarcza to do codziennego użytku.

Jeśli chcesz, żeby nowe, nieznane opisy były rozumiane lepiej, możesz doinstalować lokalny
model językowy:

1. Zainstaluj Ollamę: https://ollama.com/download (Windows i Mac).
2. W terminalu lub wierszu poleceń wpisz:
   ```
   ollama pull llama3.2:3b
   ```
   Pobierze się około 2 GB.
3. Uruchom BiedaOS ponownie — znaczek w rogu zmieni się na „AI: aktywne".

Model możesz zmienić w stopce aplikacji (musi być wcześniej pobrany przez Ollamę).

---

## Dla programistów

```bash
# Środowisko
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# Uruchomienie
.venv/bin/python -m biedaos

# Testy (38 testów)
.venv/bin/pytest

# Build
# push taga v* uruchamia automatyczny build
```
