# Career Mode DB

Aplikacja do prowadzenia własnej bazy zawodników z trybu kariery w EA FC.
Dla każdego zawodnika zapisujesz sezon po sezonie: klub, wiek, OVR,
wartość transferową oraz mecze, gole (lub czyste konta) i asysty.

Dane trzymane są lokalnie w pliku SQLite (`data/career.db`) i nie są
częścią repozytorium.

## Funkcje
- wspólna baza dla wszystkich karier z filtrowaniem po grze i klubie
- ścieżka kariery zawodnika z podsumowaniem statystyk
- ulubieni zawodnicy
- wykres rozwoju OVR
- rankingi

## Uruchomienie
    pip install -r requirements.txt
    streamlit run app.py