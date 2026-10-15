import sqlite3

import pandas as pd
import streamlit as st
from db import (
    add_player, add_season, get_all_clubs, get_clubs, get_games,
    get_players, get_seasons, init_db, set_favorite,
)
from ratings import rating_style

POSITIONS = [
    "GK", "CB", "LB", "RB", "LWB", "RWB", "CDM", "CM", "CAM", "LM", "RM", "LW", "RW", "CF", "ST",
]

def parse_money(text: str):
    cleaned = text.strip().replace(".", "").replace(",", "").replace(" ","").replace("€", "")
    if not cleaned:
        return None
    if not cleaned.isdigit():
        raise ValueError
    return int(cleaned)

def format_money(value) -> str:
    if pd.isna(value):
        return "-"
    return f"{int(value):,}".replace(",", ".") + " €"

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

st.subheader("Dodaj zawodnika")
pn = st.session_state.setdefault("player_form_n", 0)

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

table = view.assign(fav=view["is_favorite"].map(lambda v: "★" if v else ""))[
    ["fav", "shown_name", "name", "position", "nationality", "age", "ovr", "max_ovr",
     "value_eur", "game", "managed_club", "original_club", "matches", "goals", "assists"]
].rename(columns={
    "fav": "",
    "shown_name": "Zawodnik",
    "name": "Pełna nazwa",
    "position": "Pozycja",
    "nationality": "Narodowość",
    "age": "Wiek",
    "ovr": "OVR",
    "max_ovr": "Max OVR",
    "value_eur": "Wartość",
    "game": "Gra",
    "managed_club": "Mój klub",
    "original_club": "Klub początkowy",
    "matches": "Mecze",
    "goals": "G/CS",
    "assists": "Asysty",
})

styled = (
    table.style
    .map(rating_style, subset=["OVR", "Max OVR"])
    .format(
        {"Wiek": "{:.0f}", "OVR": "{:.0f}", "Max OVR": "{:.0f}", "Wartość": format_money},
        na_rep="-",
    )
)
st.dataframe(styled, hide_index=True)

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

sn = st.session_state.setdefault("season_form_n", 0)

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

seasons = get_seasons(player_id)
if seasons:
    sdf = pd.DataFrame([dict(s) for s in seasons]).rename(columns={
        "season": "Sezon",
        "age": "Wiek",
        "ovr": "OVR",
        "value_eur": "Wartość",
        "matches": "Mecze",
        "goals": goals_label,
        "assists": "Asysty",
    })
    st.dataframe(
        sdf.style.map(rating_style, subset=["OVR"]).format({"Wartość": format_money}, na_rep="-"),
        hide_index=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Mecze razem", int(sdf["Mecze"].sum()))
    m2.metric(f"{goals_label} razem", int(sdf[goals_label].sum()))
    m3.metric("Asysty razem", int(sdf["Asysty"].sum()))
    m4.metric("Max OVR", int(sdf["OVR"].max()))
else:
    st.write("Ten zawodnik nie ma jeszcze żadnych sezonów.")