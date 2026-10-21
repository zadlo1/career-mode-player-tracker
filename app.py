import sqlite3

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from db import (
    add_player, add_season, delete_player, delete_season, get_all_clubs, get_all_seasons, get_clubs,
    get_games, get_players, get_seasons, init_db, set_favorite,
    update_player, update_season,
)
from club_logos import delete_logo, save_logo
from player_photos import delete_photo, photo_data_uri, save_photo
from ui import (
    format_money, logo_preview_html, player_header_html, players_table_html, seasons_table_html,
)
from potential import MATURE_AGE, MIN_TRAIN_PLAYERS, estimate_potentials, train_from_rows
from season_utils import is_valid_season, next_season
from countries import CODES, country_name
from charts import TEXT_DARK, TEXT_LIGHT, ovr_chart, value_chart
from rankings import render_rankings

player_table = components.declare_component(
    "player_table", path=str(Path(__file__).parent / "player_table_component")
)

POSITIONS = [
    "GK", "CB", "LB", "RB", "LWB", "RWB", "CDM", "CM", "CAM", "LM", "RM", "LW", "RW", "CF", "ST",
]

SORT_OPTIONS = {
    "Zawodnik": "shown_name",
    "Max OVR": "max_ovr",
    "Wiek": "age",
    "Max wartość": "max_value",
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

def suggest_next_season(seasons, default_position: str) -> dict:
    if not seasons:
        return {"season": "", "position": default_position, "age": 18, "ovr": 60, "value": ""}
    last = seasons[-1]
    return {
        "season": next_season(last["season"]),
        "position": last["position"] or default_position,
        "age": min(last["age"] + 1, 50) if last["age"] is not None else 18,
        "ovr": last["ovr"] if last["ovr"] is not None else 60,
        "value": "" if last["value_eur"] is None else format_money(last["value_eur"]).replace(" €", ""),
    }


def position_index(position, options=POSITIONS) -> int:
    return options.index(position) if position in options else 0


def season_position_options(player_position: str) -> list:
    if player_position == "GK":
        return ["GK"]
    return [p for p in POSITIONS if p != "GK"]


st.set_page_config(page_title="Career Mode DB", layout="wide")
init_db()

st.title("Baza zawodników - Career Mode")

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

page = st.sidebar.radio("Widok", ["Zawodnicy", "Rankingi"])

st.sidebar.header("Filtry")
search = st.sidebar.text_input("Szukaj zawodnika", help="Szuka też po pełnym imieniu i nazwisku.")
game_filter = st.sidebar.selectbox("Gra", options=get_games(), index=None, placeholder="Wszystkie")
club_filter = st.sidebar.selectbox("Mój klub", options=get_clubs(), index=None, placeholder="Wszystkie")
fav_only = st.sidebar.checkbox("Tylko ulubieni")
type_filter = st.sidebar.selectbox(
    "Typ zawodnika", ["Wszyscy", "Prawdziwi", "Wygenerowani przez grę"]
)
sort_label = st.sidebar.selectbox("Sortuj po", list(SORT_OPTIONS), index=1)
descending = st.sidebar.checkbox("Malejąco", value=True)

if page == "Rankingi":
    render_rankings(game_filter, club_filter, fav_only, type_filter)
    st.stop()

pn = st.session_state.setdefault("player_form_n", 0)

with st.expander("Dodaj zawodnika"):
    with st.form("add_player"):
        col1, col2 = st.columns(2)
        name = col1.text_input("Imię i nazwisko (pełne)", key=f"p_name_{pn}")
        display_name = col2.text_input("Wyświetlana nazwa (opcjonalnie)", key=f"p_display_{pn}")

        col3, col4 = st.columns(2)
        position = col3.selectbox("Pozycja", POSITIONS, key=f"p_pos_{pn}")
        nationality = col4.selectbox(
            "Narodowość",
            options=CODES,
            format_func=country_name,
            index=None,
            placeholder="Wybierz kraj",
            key=f"p_nat_{pn}",
        )

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

        is_generated = st.checkbox(
            "Zawodnik wygenerowany przez grę (nie istnieje naprawdę)",
            help="Np. junior z akademii albo zawodnik bez licencji.",
            key=f"p_gen_{pn}",
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
                nationality or None,
                int(game.strip()),
                managed_club.strip(),
                original_club.strip() if original_club else None,
                is_generated,
            )
            st.session_state["flash"] = f"Dodano: {display_name.strip() or name.strip()}"
            st.session_state["player_form_n"] += 1
            st.rerun()

ln = st.session_state.setdefault("logo_form_n", 0)

with st.expander("Loga klubów"):
    logo_clubs = get_all_clubs()
    if not logo_clubs:
        st.write("Najpierw dodaj zawodnika, żeby pojawił się klub.")
    else:
        logo_club = st.selectbox("Klub", logo_clubs, key="logo_club")
        st.html(logo_preview_html(logo_club))

        with st.form(f"logo_form_{ln}"):
            logo_file = st.file_uploader(
                "Wgraj logo (PNG, JPG, WebP lub SVG, do 2 MB)",
                type=["png", "jpg", "jpeg", "webp", "svg"],
                key=f"logo_file_{ln}",
            )
            lb1, lb2, _ = st.columns([1, 1, 4])
            save_logo_clicked = lb1.form_submit_button("Zapisz logo")
            delete_logo_clicked = lb2.form_submit_button("Usuń logo")

        if save_logo_clicked:
            if logo_file is None:
                st.error("Wybierz plik z logo.")
            else:
                try:
                    save_logo(logo_club, logo_file.getvalue(), logo_file.name)
                except ValueError as error:
                    st.error(str(error))
                else:
                    st.session_state["flash"] = f"Zapisano logo: {logo_club}"
                    st.session_state["logo_form_n"] += 1
                    st.rerun()

        if delete_logo_clicked:
            if delete_logo(logo_club):
                st.session_state["flash"] = f"Usunięto logo: {logo_club}"
                st.session_state["logo_form_n"] += 1
                st.rerun()
            else:
                st.info("Ten klub nie ma zapisanego logo.")

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
if type_filter == "Prawdziwi":
    view = view[view["is_generated"] == 0]
elif type_filter == "Wygenerowani przez grę":
    view = view[view["is_generated"] == 1]

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

clicked = player_table(html=players_table_html(view, clickable=True), key="players_table", default=None)
if clicked and st.session_state.get("table_click") != clicked["t"]:
    st.session_state["table_click"] = clicked["t"]
    if clicked["id"] in set(view["id"]):
        st.session_state["player_select"] = clicked["id"]
        st.session_state["scroll_to_player"] = True

st.subheader("Sezony zawodnika")

by_id = {r["id"]: r for r in view.to_dict("records")}
if st.session_state.get("player_select") not in by_id:
    st.session_state.pop("player_select", None)
player_id = st.selectbox(
    "Zawodnik",
    options=list(by_id.keys()),
    key="player_select",
    format_func=lambda pid: (
        f"{by_id[pid]['shown_name']} (FC {by_id[pid]['game']}"
        + (f", {by_id[pid]['original_club']})" if clean(by_id[pid]["original_club"]) else ")")
    ),
)
player = by_id[player_id]
if st.session_state.pop("scroll_to_player", False):
    components.html(
        """<script>
        setTimeout(() => {
          const doc = window.parent.document;
          const el = doc.getElementById("sezony-zawodnika")
            || [...doc.querySelectorAll("h3")].find(h => h.textContent.includes("Sezony zawodnika"));
          if (el) el.scrollIntoView({behavior: "smooth", block: "start"});
        }, 300);
        </script>""",
        height=0,
    )
goals_label = "Czyste konta" if player["position"] == "GK" else "Gole"
season_positions = season_position_options(player["position"])

st.html(player_header_html(player, photo_data_uri(player_id)))

phn = st.session_state.setdefault("photo_form_n", 0)

with st.expander("Zdjęcie zawodnika"):
    with st.form(f"photo_form_{player_id}_{phn}"):
        photo_file = st.file_uploader(
            "Wgraj zdjęcie (PNG, JPG lub WebP, do 2 MB)",
            type=["png", "jpg", "jpeg", "webp"],
            key=f"photo_file_{player_id}_{phn}",
        )
        ph1, ph2, _ = st.columns([1, 1, 4])
        save_photo_clicked = ph1.form_submit_button("Zapisz zdjęcie")
        delete_photo_clicked = ph2.form_submit_button("Usuń zdjęcie")

    if save_photo_clicked:
        if photo_file is None:
            st.error("Wybierz plik ze zdjęciem.")
        else:
            try:
                save_photo(player_id, photo_file.getvalue(), photo_file.name)
            except ValueError as error:
                st.error(str(error))
            else:
                st.session_state["flash"] = f"Zapisano zdjęcie: {player['shown_name']}"
                st.session_state["photo_form_n"] += 1
                st.rerun()

    if delete_photo_clicked:
        if delete_photo(player_id):
            st.session_state["flash"] = f"Usunięto zdjęcie: {player['shown_name']}"
            st.session_state["photo_form_n"] += 1
            st.rerun()
        else:
            st.info("Ten zawodnik nie ma zapisanego zdjęcia.")

is_fav = bool(player["is_favorite"])
fav = st.checkbox("Ulubiony", value=is_fav, key=f"fav_{player_id}")
if fav != is_fav:
    set_favorite(player_id, fav)
    st.rerun()

seasons = get_seasons(player_id)
if seasons:
    raw = pd.DataFrame([dict(s) for s in seasons])
    raw["position"] = raw["position"].fillna(player["start_position"])
    pot_model = train_from_rows(
        [dict(s) for s in get_all_seasons()], df.set_index("id")["start_position"].to_dict()
    )
    estimates = estimate_potentials(raw.to_dict("records"), player["start_position"], pot_model)
    raw["pot"] = [e["pot"] if e else None for e in estimates]
    raw["pot_has_value"] = [e["has_value"] if e else True for e in estimates]
    st.html(seasons_table_html(raw, goals_label, goalkeeper=player["position"] == "GK"))

    if pot_model.active:
        st.caption(
            f"POT (szac.) jest skalibrowany na Twojej bazie: {pot_model.mature_players} zawodników "
            f"w wieku {MATURE_AGE}+ i {pot_model.samples} ich sezonów."
        )
    else:
        st.caption(
            f"POT (szac.) liczony wzorem bazowym. Do nauki na Twojej bazie potrzeba min. "
            f"{MIN_TRAIN_PLAYERS} zawodników w wieku {MATURE_AGE}+ (teraz: {pot_model.mature_players})."
        )

    if len(raw) >= 2:
        label_color = TEXT_LIGHT if st.context.theme.type == "dark" else TEXT_DARK
        chart_ovr, chart_value = st.columns(2)
        with chart_ovr:
            st.caption("Rozwój OVR (przerywana linia: szacowany potencjał)")
            st.altair_chart(ovr_chart(raw, label_color), width="stretch")
        with chart_value:
            st.caption("Wartość transferowa")
            if raw["value_eur"].notna().sum() >= 2:
                st.altair_chart(value_chart(raw, label_color), width="stretch")
            else:
                st.caption("Wykres wartości pojawi się, gdy dwa sezony będą miały podaną wartość.")
    else:
        st.caption("Wykresy rozwoju OVR i wartości pojawią się po dodaniu drugiego sezonu.")
else:
    st.write("Ten zawodnik nie ma jeszcze żadnych sezonów.")

sn = st.session_state.setdefault("season_form_n", 0)
suggestion = suggest_next_season(seasons, player["position"])
fk = f"{player_id}_{sn}"

with st.expander("Dodaj sezon"):
    if seasons:
        st.caption("Pola są wypełnione propozycją na podstawie poprzedniego sezonu, możesz je zmienić.")

    with st.form("add_season"):
        c1, cp, c2, c3, c4 = st.columns(5)
        season = c1.text_input(
            "Sezon", value=suggestion["season"], placeholder="2026/27 lub 2026", key=f"s_season_{fk}"
        )
        s_position = cp.selectbox(
            "Pozycja",
            season_positions,
            index=position_index(suggestion["position"], season_positions),
            key=f"s_pos_{fk}",
        )
        age = c2.number_input(
            "Wiek", min_value=14, max_value=50, value=suggestion["age"], step=1, key=f"s_age_{fk}"
        )
        ovr = c3.number_input(
            "OVR", min_value=0, max_value=99, value=suggestion["ovr"], step=1, key=f"s_ovr_{fk}"
        )
        value_text = c4.text_input(
            "Wartość (€)", value=suggestion["value"], placeholder="3.000.000", key=f"s_value_{fk}"
        )

        c5, c6, c7 = st.columns(3)
        matches = c5.number_input("Mecze", min_value=0, value=0, step=1, key=f"s_matches_{fk}")
        goals = c6.number_input(goals_label, min_value=0, value=0, step=1, key=f"s_goals_{fk}")
        assists = c7.number_input("Asysty", min_value=0, value=0, step=1, key=f"s_assists_{fk}")

        season_submitted = st.form_submit_button("Dodaj sezon")

    if season_submitted:
        if not is_valid_season(season):
            st.error("Sezon wpisz jako 2026/27 (przełom lat) albo 2026 (jeden rok).")
        else:
            try:
                value_eur = parse_money(value_text)
            except ValueError:
                st.error("Wartość wpisz samymi cyframi, np. 3.000.000 lub 4000000")
            else:
                try:
                    add_season(player_id, season.strip(), s_position, int(age), int(ovr), value_eur,
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
    nat_value = clean(player["nationality"])

    with st.form(f"edit_player_{player_id}"):
        e1, e2 = st.columns(2)
        e_name = e1.text_input("Imię i nazwisko (pełne)", value=clean(player["name"]), key=f"e_name_{player_id}")
        e_display = e2.text_input("Wyświetlana nazwa (opcjonalnie)", value=clean(player["display_name"]), key=f"e_disp_{player_id}")

        e3, e4 = st.columns(2)
        e_pos = e3.selectbox(
            "Pozycja początkowa",
            POSITIONS,
            index=position_index(player["start_position"]),
            key=f"e_pos_{player_id}",
        )
        e_nat = e4.selectbox(
            "Narodowość",
            options=CODES,
            format_func=country_name,
            index=CODES.index(nat_value) if nat_value in CODES else None,
            placeholder="Wybierz kraj",
            key=f"e_nat_{player_id}",
        )

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

        e_gen = st.checkbox(
            "Zawodnik wygenerowany przez grę (nie istnieje naprawdę)",
            value=bool(player["is_generated"]),
            help="Np. junior z akademii albo zawodnik bez licencji.",
            key=f"e_gen_{player_id}",
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
                e_nat or None,
                int(e_game.strip()),
                e_club.strip(),
                e_orig.strip() if e_orig else None,
                e_gen,
            )
            st.session_state["flash"] = f"Zapisano zmiany: {e_display.strip() or e_name.strip()}"
            st.rerun()

    if del_p:
        if not confirm_p:
            st.error("Zaznacz potwierdzenie, aby usunąć zawodnika.")
        else:
            delete_player(player_id)
            delete_photo(player_id)
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
            index=len(by_season) - 1,
            key=f"es_sel_{player_id}_{sn}",
        )
        s = by_season[sid]
        value_plain = "" if s["value_eur"] is None else format_money(s["value_eur"]).replace(" €", "")

        current_pos = s["position"] or player["position"]
        edit_positions = season_positions if current_pos in season_positions else [current_pos] + season_positions

        with st.form(f"edit_season_{sid}"):
            f1, fp, f2, f3, f4 = st.columns(5)
            es_season = f1.text_input("Sezon", value=s["season"], key=f"es_season_{sid}")
            es_position = fp.selectbox(
                "Pozycja",
                edit_positions,
                index=position_index(current_pos, edit_positions),
                key=f"es_pos_{sid}",
            )
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
            if not is_valid_season(es_season):
                st.error("Sezon wpisz jako 2026/27 (przełom lat) albo 2026 (jeden rok).")
            else:
                try:
                    es_value_eur = parse_money(es_value)
                except ValueError:
                    st.error("Wartość wpisz samymi cyframi, np. 3.000.000 lub 4000000")
                else:
                    try:
                        update_season(sid, es_season.strip(), es_position, int(es_age), int(es_ovr),
                                      es_value_eur, int(es_matches), int(es_goals), int(es_assists))
                        st.session_state["flash"] = f"Zapisano zmiany w sezonie {es_season.strip()}"
                        st.session_state["season_form_n"] += 1
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(f"Ten zawodnik ma już zapisany sezon {es_season.strip()}.")

        if del_s:
            if not confirm_s:
                st.error("Zaznacz potwierdzenie, aby usunąć sezon.")
            else:
                delete_season(sid)
                st.session_state["flash"] = f"Usunięto sezon {s['season']}"
                st.session_state["season_form_n"] += 1
                st.rerun()