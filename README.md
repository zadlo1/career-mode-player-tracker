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
- szacowany potencjał (POT) przy każdym sezonie: model dopasowany do ok. 14 tys. zawodników FC 26 (OVR, wiek, wartość), z korektą na tempo rozwoju, grę w sezonie i zawodników z Twojej bazy, którzy skończyli rozwój (`potential.py`, współczynniki w `potential_coefs.py`, odtworzenie: `python tools/fit_potential_model.py plik.csv`)
- podsumowanie sezonów oraz wykresy rozwoju OVR i wartości transferowej
- edycja i usuwanie zawodników oraz sezonów
- rankingi (top 10): strzelcy, czyste konta, asysty, najdroższy zawodnik, największy rozwój OVR
- aktualizacja sezonu: początek (nowe sezony dla całej kadry naraz, z odejściami i nowymi zawodnikami)
  i koniec (statystyki całej kadry w jednej tabeli); status zawodnika (w kadrze / odszedł / emerytura)
- rankingi pojedynczych sezonów (najlepszy sezon wg G+A, gole, asysty, czyste konta, G+A na mecz,
  największy skok OVR); przełącznik „Rodzaj rankingu” w widoku Rankingi
- statystyki na mecz (gole, asysty, % czystych kont) w tabeli sezonów i w rankingach z progiem
  minimalnej liczby meczów;
- loga klubów wgrywane przez użytkownika (PNG, JPG, WebP, SVG), pokazywane na liście i w rankingach
- zdjęcia zawodników wgrywane przez użytkownika (PNG, JPG, WebP), pokazywane w karcie zawodnika;
  zapisywane jako pliki w `data/images/players/`


## Uruchomienie
    pip install -r requirements.txt
    streamlit run app.py

Flagi państw są w `assets/flags`. Gdyby folder był pusty, pobierzesz je poleceniem:

    python download_flags.py

## Model potencjału
Współczynniki modelu (`potential_coefs.py`) powstały na danych z
[jawadk05/Fc26-dataset-analysis](https://github.com/jawadk05/Fc26-dataset-analysis)
(`FC26_20250921.csv`, stan z 19.09.2025). Plik CSV nie jest częścią repozytorium.

Odtworzenie współczynników:

    python tools/fit_potential_model.py FC26_20250921.csv 2025-07-01

## Licencje
Flagi pochodzą z projektu [flag-icons](https://github.com/lipis/flag-icons)
na licencji MIT (kopia licencji w `assets/flags/LICENSE-flag-icons.txt`).
Projekt nie zawiera żadnych grafik ani danych należących do EA.