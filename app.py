import sqlite3

import pandas as pd
import streamlit as st
from db import (
    add_player, add_season, delete_player, delete_season, get_all_clubs, get_clubs,
    get_games, get_players, get_seasons, init_db, set_favorite,
    update_player, update_season,
)
from ui import format_money, players_table_html, seasons_table_html

POSITIONS = [
    "GK", "CB", "LB", "RB", "LWB", "RWB", "CDM", "CM", "CAM", "LM", "RM", "LW", "RW", "CF", "ST",
]

SORT_OPTIONS = {
    "Zawodnik": "shown_name",
    "OVR": "ovr",
    "Max OVR": "max_ovr",
    "Wiek": "age",
    "Wartość": "value_eur",
    "Mecze": "matches",
    "Gole / czyste konta": "goals",
    "Asysty": "assists",
}

def parse_money(text: str):
    cleaned = text.strip().replace(".", "").replace(",", "").replace(" ","").replace("€", "")
    if not cleaned:
        return None
    if not cleaned.isdigit():
        raise ValueError
    return int(cleaned)

def clean(value) -> str:
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return ""
    return str(value)

st.set_page_config(page_title="Career Mode DB", layout="wide")
init_db()

st.title("Baza zawodników - Career Mode")

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

st.sidebar.header("Filtry")
search = st.sidebar.text_input("Szukaj zawodnika")
game_filter = st.sidebar.selectbox("Gra", options=get_games(), index=None, placeholder="Wszystkie")
club_filter = st.sidebar.selectbox("Mój klub", options=get_clubs(), index=None, placeholder="Wszystkie")
fav_only = st.sidebar.checkbox("Tylko ulubieni")
sort_label = st.sidebar.selectbox("Sortuj po", list(SORT_OPTIONS), index=1)
descending = st.sidebar.checkbox("Malejąco", value=True)

st.subheader("Dodaj zawodnika")
pn = st.session_state.setdefault("player_form_n", 0)

with st.expander("Dodaj zawodnika"):
    with st.form("add_player"):
        col1, col2 = st.columns(2)
        name = col1.text_input("Imię i nazwisko (pełne)", key=f"p_name_{pn}")
        display_name = col2.text_input("Wyświetlana nazwa (opcjonalnie)", key=f"p_display_{pn}")

        col3, col4 = st.columns(2)
        position = col3.selectbox("Pozycja", POSITIONS, key=f"p_pos_{pn}")
        nationality = col4.text_input("Narodowość", key=f"p_nat_{pn}")

        col5, col6 = st.columns(2)
        game = col5.selectbox(
            "Numer gry (np. 26)",
            options=[str(g) for g in get_games()],
            index=None,
            accept_new_options=True,
            placeholder="Wybierz lub wpisz nowy",
            key=f"p_game_{pn}",
        )
        managed_club = col6.selectbox(
            "Klub, którym prowadzę karierę",
            options=get_clubs(),
            index=None,
            accept_new_options=True,
            placeholder="Wybierz lub wpisz nowy",
            key=f"p_club_{pn}",
        )
        original_club = st.selectbox(
            "Klub początkowy zawodnika (opcjonalnie)",
            options=get_all_clubs(),
            index=None,
            accept_new_options=True,
            placeholder="Wybierz lub wpisz nowy",
            key=f"p_orig_{pn}",
        )

        submitted = st.form_submit_button("Dodaj zawodnika")

    if submitted:
        if not name.strip() or not managed_club or not game:
            st.error("Imię i nazwisko, numer gry oraz klub są wymagane.")
        elif not game.strip().isdigit():
            st.error("Numer gry - wpisz samą liczbę, np. 26")
        else:
            add_player(
                name.strip(),
                display_name.strip() or None,
                position,
                nationality.strip(),
                int(game.strip()),
                managed_club.strip(),
                original_club.strip() if original_club else None,
            )
            st.session_state["flash"] = f"Dodano: {display_name.strip() or name.strip()}"
            st.session_state["player_form_n"] += 1
            st.rerun()

st.subheader("Zawodnicy")
players = get_players()
if not players:
    st.write("Baza jest jeszcze pusta. Dodaj pierwszego zawodnika.")
    st.stop()

df = pd.DataFrame([dict(player) for player in players])
for col in ["matches", "goals", "assists"]:
    df[col] = df[col].fillna(0).astype(int)

view = df
if search.strip():
    q = search.strip()
    view = view[
        view["shown_name"].str.contains(q, case=False, na=False, regex=False)
        | view["name"].str.contains(q, case=False, na=False, regex=False)
    ]
if game_filter is not None:
    view = view[view["game"] == game_filter]
if club_filter is not None:
    view = view[view["managed_club"] == club_filter]
if fav_only:
    view = view[view["is_favorite"] == 1]

if view.empty:
    st.info("Brak zawodników pasujących do filtrów.")
    st.stop()

st.caption(f"Zawodników w widoku: {len(view)} z {len(df)}")

view = view.sort_values(
    SORT_OPTIONS[sort_label],
    ascending=not descending,
    na_position="last",
    key=lambda s: s.str.lower() if pd.api.types.is_string_dtype(s) else s,
)

st.html(players_table_html(view))

st.subheader("Sezony zawodnika")

by_id = {r["id"]: r for r in view.to_dict("records")}
player_id = st.selectbox(
    "Zawodnik",
    options=list(by_id.keys()),
    format_func=lambda pid: f"{by_id[pid]['shown_name']} (FC {by_id[pid]['game']}, {by_id[pid]['managed_club']})",
)
player = by_id[player_id]
goals_label = "Czyste konta" if player["position"] == "GK" else "Gole"

is_fav = bool(player["is_favorite"])
fav = st.checkbox("Ulubiony", value=is_fav, key=f"fav_{player_id}")
if fav != is_fav:
    set_favorite(player_id, fav)
    st.rerun()

seasons = get_seasons(player_id)
if seasons:
    raw = pd.DataFrame([dict(s) for s in seasons])
    st.html(seasons_table_html(raw, goals_label))
else:
    st.write("Ten zawodnik nie ma jeszcze żadnych sezonów.")

sn = st.session_state.setdefault("season_form_n", 0)

with st.expander("Dodaj sezon"):
    with st.form("add_season"):
        c1, c2, c3, c4 = st.columns(4)
        season = c1.text_input("Sezon", placeholder="26/27", key=f"s_season_{sn}")
        age = c2.number_input("Wiek", min_value=14, max_value=50, value=18, step=1, key=f"s_age_{sn}")
        ovr = c3.number_input("OVR", min_value=0, max_value=99, value=60, step=1, key=f"s_ovr_{sn}")
        value_text = c4.text_input("Wartość (€)", placeholder="3.000.000", key=f"s_value_{sn}")

        c5, c6, c7 = st.columns(3)
        matches = c5.number_input("Mecze", min_value=0, value=0, step=1, key=f"s_matches_{sn}")
        goals = c6.number_input(goals_label, min_value=0, value=0, step=1, key=f"s_goals_{sn}")
        assists = c7.number_input("Asysty", min_value=0, value=0, step=1, key=f"s_assists_{sn}")

        season_submitted = st.form_submit_button("Dodaj sezon")

    if season_submitted:
        if not season.strip():
            st.error("Podaj sezon, np. 26/27.")
        else:
            try:
                value_eur = parse_money(value_text)
            except ValueError:
                st.error("Wartość wpisz samymi cyframi, np. 3.000.000 lub 4000000")
            else:
                try:
                    add_season(player_id, season.strip(), int(age), int(ovr), value_eur,
                               int(matches), int(goals), int(assists))
                    st.session_state["flash"] = f"Dodano sezon: {season.strip()}"
                    st.session_state["season_form_n"] += 1
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(f"Ten zawodnik ma już zapisany sezon {season.strip()}.")

with st.expander("Edytuj lub usuń zawodnika"):
    games = [str(g) for g in get_games()]
    clubs = get_clubs()
    all_clubs = get_all_clubs()
    orig = clean(player["original_club"])
    pos_index = POSITIONS.index(player["position"]) if player["position"] in POSITIONS else 0

    with st.form(f"edit_player_{player_id}"):
        e1, e2 = st.columns(2)
        e_name = e1.text_input("Imię i nazwisko (pełne)", value=clean(player["name"]), key=f"e_name_{player_id}")
        e_display = e2.text_input("Wyświetlana nazwa (opcjonalnie)", value=clean(player["display_name"]), key=f"e_disp_{player_id}")

        e3, e4 = st.columns(2)
        e_pos = e3.selectbox("Pozycja", POSITIONS, index=pos_index, key=f"e_pos_{player_id}")
        e_nat = e4.text_input("Narodowość", value=clean(player["nationality"]), key=f"e_nat_{player_id}")

        e5, e6 = st.columns(2)
        e_game = e5.selectbox(
            "Numer gry",
            options=games,
            index=games.index(str(player["game"])),
            accept_new_options=True,
            key=f"e_game_{player_id}",
        )
        e_club = e6.selectbox(
            "Klub, którym prowadzę karierę",
            options=clubs,
            index=clubs.index(player["managed_club"]),
            accept_new_options=True,
            key=f"e_club_{player_id}",
        )
        e_orig = st.selectbox(
            "Klub początkowy zawodnika (opcjonalnie)",
            options=all_clubs,
            index=all_clubs.index(orig) if orig in all_clubs else None,
            accept_new_options=True,
            placeholder="Brak",
            key=f"e_orig_{player_id}",
        )

        confirm_p = st.checkbox(
            "Potwierdzam usunięcie zawodnika wraz ze wszystkimi jego sezonami",
            key=f"e_confirm_{player_id}",
        )
        b1, b2, _ = st.columns([1, 1, 4])
        save_p = b1.form_submit_button("Zapisz zmiany")
        del_p = b2.form_submit_button("Usuń zawodnika")

    if save_p:
        if not e_name.strip() or not e_club or not e_game:
            st.error("Imię i nazwisko, numer gry oraz klub są wymagane.")
        elif not e_game.strip().isdigit():
            st.error("Numer gry - wpisz samą liczbę, np. 26")
        else:
            update_player(
                player_id,
                e_name.strip(),
                e_display.strip() or None,
                e_pos,
                e_nat.strip(),
                int(e_game.strip()),
                e_club.strip(),
                e_orig.strip() if e_orig else None,
            )
            st.session_state["flash"] = f"Zapisano zmiany: {e_display.strip() or e_name.strip()}"
            st.rerun()

    if del_p:
        if not confirm_p:
            st.error("Zaznacz potwierdzenie, aby usunąć zawodnika.")
        else:
            delete_player(player_id)
            st.session_state["flash"] = f"Usunięto zawodnika: {player['shown_name']}"
            st.rerun()

with st.expander("Edytuj lub usuń sezon"):
    if not seasons:
        st.write("Ten zawodnik nie ma jeszcze sezonów do edycji.")
    else:
        by_season = {s["id"]: dict(s) for s in seasons}
        sid = st.selectbox(
            "Sezon",
            options=list(by_season),
            format_func=lambda i: by_season[i]["season"],
            key=f"es_sel_{player_id}",
        )
        s = by_season[sid]
        value_plain = "" if s["value_eur"] is None else format_money(s["value_eur"]).replace(" €", "")

        with st.form(f"edit_season_{sid}"):
            f1, f2, f3, f4 = st.columns(4)
            es_season = f1.text_input("Sezon", value=s["season"], key=f"es_season_{sid}")
            es_age = f2.number_input("Wiek", min_value=14, max_value=50,
                                     value=s["age"] if s["age"] is not None else 18,
                                     step=1, key=f"es_age_{sid}")
            es_ovr = f3.number_input("OVR", min_value=0, max_value=99,
                                     value=s["ovr"] if s["ovr"] is not None else 60,
                                     step=1, key=f"es_ovr_{sid}")
            es_value = f4.text_input("Wartość (€)", value=value_plain, key=f"es_value_{sid}")

            f5, f6, f7 = st.columns(3)
            es_matches = f5.number_input("Mecze", min_value=0, value=s["matches"], step=1, key=f"es_matches_{sid}")
            es_goals = f6.number_input(goals_label, min_value=0, value=s["goals"], step=1, key=f"es_goals_{sid}")
            es_assists = f7.number_input("Asysty", min_value=0, value=s["assists"], step=1, key=f"es_assists_{sid}")

            confirm_s = st.checkbox("Potwierdzam usunięcie tego sezonu", key=f"es_confirm_{sid}")
            sb1, sb2, _ = st.columns([1, 1, 4])
            save_s = sb1.form_submit_button("Zapisz zmiany")
            del_s = sb2.form_submit_button("Usuń sezon")

        if save_s:
            if not es_season.strip():
                st.error("Podaj sezon, np. 26/27.")
            else:
                try:
                    es_value_eur = parse_money(es_value)
                except ValueError:
                    st.error("Wartość wpisz samymi cyframi, np. 3.000.000 lub 4000000")
                else:
                    try:
                        update_season(sid, es_season.strip(), int(es_age), int(es_ovr), es_value_eur,
                                      int(es_matches), int(es_goals), int(es_assists))
                        st.session_state["flash"] = f"Zapisano zmiany w sezonie {es_season.strip()}"
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(f"Ten zawodnik ma już zapisany sezon {es_season.strip()}.")

        if del_s:
            if not confirm_s:
                st.error("Zaznacz potwierdzenie, aby usunąć sezon.")
            else:
                delete_season(sid)
                st.session_state["flash"] = f"Usunięto sezon {s['season']}"
                st.rerun()