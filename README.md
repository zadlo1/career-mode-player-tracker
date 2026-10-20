# Career Mode DB

Aplikacja do prowadzenia własnej bazy zawodników z trybu kariery w EA FC.
Dla każdego zawodnika zapisujesz sezon po sezonie: pozycję, wiek, OVR,
wartość transferową oraz mecze, gole (lub czyste konta) i asysty.

Dane trzymane są lokalnie w pliku SQLite (`data/career.db`), a wgrane loga
i zdjęcia w `data/images/`. Nic z tego nie jest częścią repozytorium.

## Funkcje
- wspólna baza dla wszystkich karier: filtrowanie po grze i klubie, wyszukiwarka, sortowanie
- zawodnik: wyświetlana nazwa, narodowość z flagą, klub początkowy, ulubieni
- oznaczanie zawodników wygenerowanych przez grę (juniorzy, brak licencji) i filtr po typie
- sezon po sezonie: pozycja, wiek, OVR, wartość, mecze, gole (lub czyste konta), asysty
- propozycja kolejnego sezonu (rok, wiek, OVR, wartość) na podstawie poprzedniego
- podsumowanie sezonów oraz wykresy rozwoju OVR i wartości transferowej
- edycja i usuwanie zawodników oraz sezonów
- rankingi (top 10): strzelcy, czyste konta, asysty, najdroższy zawodnik, największy rozwój OVR
- statystyki na mecz (gole, asysty, % czystych kont) w tabeli sezonów i w rankingach z progiem
  minimalnej liczby meczów;
- loga klubów wgrywane przez użytkownika (PNG, JPG, WebP, SVG), pokazywane na liście i w rankingach
- przy zawodniku pokazywany jest jego klub początkowy z logiem
- zdjęcia zawodników wgrywane przez użytkownika (PNG, JPG, WebP), pokazywane w karcie zawodnika;
  zapisywane jako pliki w `data/images/players/`

## Uruchomienie
    pip install -r requirements.txt
    streamlit run app.py

Flagi państw są w `assets/flags`. Gdyby folder był pusty, pobierzesz je poleceniem:

    python download_flags.py

## Licencje
Flagi pochodzą z projektu [flag-icons](https://github.com/lipis/flag-icons)
na licencji MIT (kopia licencji w `assets/flags/LICENSE-flag-icons.txt`).
Projekt nie zawiera żadnych grafik ani danych należących do EA.