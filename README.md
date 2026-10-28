# Career Mode Tracker

Aplikacja do prowadzenia własnej bazy kariery w EA FC: zawodnicy, sezony, kluby i rozgrywki.
Dane trzymane są lokalnie (baza w `data/`) i nie są częścią repozytorium.

Projekt jest w trakcie przebudowy na FastAPI + HTMX. Poprzednia wersja (Streamlit) jest
dostępna w wydaniu `v1-streamlit`.

## Wymagania
- [uv](https://docs.astral.sh/uv/) (zarządza Pythonem i bibliotekami)

Instalacja uv na Windowsie:

    winget install --id=astral-sh.uv -e

## Uruchomienie

    uv sync
    uv run careertracker

Aplikacja działa pod adresem http://127.0.0.1:8000. Do pracy nad kodem:

    uv run careertracker --reload

## Testy

    uv run pytest

## Struktura

    src/careertracker/
      domain/     czysta logika (bez bazy i bez WWW)
      db/         modele i migracje bazy
      services/   przypadki użycia
      web/        FastAPI, szablony Jinja, HTMX, pliki statyczne
    tests/
    data/         baza i grafiki (poza gitem)

## Licencje
HTMX (`src/careertracker/web/static/htmx.min.js`) na licencji 0BSD, kopia w `LICENSE-htmx.txt`.
Projekt nie zawiera żadnych grafik ani danych należących do EA.