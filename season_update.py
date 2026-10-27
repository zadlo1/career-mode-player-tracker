import sqlite3

import pandas as pd
import streamlit as st

from db import (
    apply_season_start, get_all_seasons, get_career_season_rows, get_career_seasons,
    get_players, update_season_stats,
)
from ratings import POSITION_GROUPS
from season_utils import is_valid_season, next_season

POSITIONS = list(POSITION_GROUPS)
GROUP_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "ATT": 3}

STATUS_ACTIVE = "W kadrze"
STATUS_LEFT = "Odszedł"
STATUS_RETIRED = "Emerytura"
STATUS_SKIP = "Pomiń"
STATUSES = [STATUS_ACTIVE, STATUS_LEFT, STATUS_RETIRED, STATUS_SKIP]

START_MODE = "Początek sezonu"
END_MODE = "Koniec sezonu"

START_COLUMNS = ["id", "Zawodnik", "Status", "Dokąd", "Poz.", "Wiek", "OVR", "Wartość (€)", "Uwagi"]
STATS_COLUMNS = ["Mecze", "Gole / CS", "Asysty"]


# ---------- drobne pomocniki ----------

def _blank(value) -> bool:
    return value is None or (not isinstance(value, str) and pd.isna(value))


def _text(value) -> str:
    return "" if _blank(value) else str(value).strip()


def parse_money(value):
    cleaned = _text(value).replace(".", "").replace(",", "").replace(" ", "").replace("€", "")
    if not cleaned:
        return None
    if not cleaned.isdigit():
        raise ValueError
    return int(cleaned)


def format_plain_money(value) -> str:
    if _blank(value):
        return ""
    return f"{int(value):,}".replace(",", ".")


def _group_rank(position) -> int:
    return GROUP_ORDER.get(POSITION_GROUPS.get(str(position).upper(), "ATT"), 3)


def _sorted_by_position(df: pd.DataFrame, position_column: str, name_column: str) -> pd.DataFrame:
    order = df[position_column].map(_group_rank)
    names = df[name_column].str.lower()
    return df.assign(_order=order, _name=names).sort_values(["_order", "_name"]).drop(columns=["_order", "_name"])


# ---------- tabela początku sezonu ----------

def build_start_table(players: pd.DataFrame, seasons: pd.DataFrame):
    """Zwraca (tabela, ostatni_sezon_kariery, {id_zawodnika: jego_ostatni_sezon}).

    Do tabeli trafiają zawodnicy bez statusu odejścia: ci, którzy mają już sezony,
    oraz nowi (bez żadnego sezonu), których wiek i OVR trzeba dopiero uzupełnić.
    """
    active = players[players["squad_status"].isna()]

    last_by_player = {}
    if not seasons.empty:
        last_by_player = seasons.groupby("player_id")["season"].max().to_dict()

    ids_with_seasons = [pid for pid in active["id"] if pid in last_by_player]
    career_latest = max((last_by_player[pid] for pid in ids_with_seasons), default=None)

    continuing, new_players = [], []
    for r in active.to_dict("records"):
        pid = r["id"]
        last = last_by_player.get(pid)
        if last is None:
            new_players.append({
                "id": pid, "Zawodnik": r["shown_name"], "Status": STATUS_ACTIVE, "Dokąd": "",
                "Poz.": r["position"], "Wiek": None, "OVR": None, "Wartość (€)": "",
                "Uwagi": "nowy zawodnik: uzupełnij wiek i OVR (albo ustaw „Pomiń”)",
            })
            continue

        stayed = last == career_latest
        age = None if _blank(r["age"]) else min(int(r["age"]) + 1, 50)
        continuing.append({
            "id": pid, "Zawodnik": r["shown_name"],
            "Status": STATUS_ACTIVE if stayed else STATUS_LEFT, "Dokąd": "",
            "Poz.": r["position"], "Wiek": age,
            "OVR": None if _blank(r["ovr"]) else int(r["ovr"]),
            "Wartość (€)": format_plain_money(r["value_eur"]),
            "Uwagi": "" if stayed else f"ostatni sezon: {last}, więc domyślnie odszedł",
        })

    frames = []
    for rows in (continuing, new_players):
        if rows:
            frames.append(_sorted_by_position(pd.DataFrame(rows, columns=START_COLUMNS), "Poz.", "Zawodnik"))
    if not frames:
        return pd.DataFrame(columns=START_COLUMNS), career_latest, last_by_player

    table = pd.concat(frames, ignore_index=True)
    table["Wiek"] = pd.array(table["Wiek"], dtype="Int64")
    table["OVR"] = pd.array(table["OVR"], dtype="Int64")
    return table, career_latest, last_by_player


def process_start_table(edited, new_label, last_by_player, labels_by_player, current_positions):
    """Sprawdza tabelę i zwraca (nowe_sezony, zmiany_statusu, błędy)."""
    errors, new_seasons, status_updates = [], [], []

    label = _text(new_label)
    if not is_valid_season(label):
        errors.append("Nowy sezon wpisz jako 2026/27 (przełom lat) albo 2026 (jeden rok).")
        return new_seasons, status_updates, errors

    for _, row in edited.iterrows():
        pid = int(row["id"])
        name = row["Zawodnik"]
        status = row["Status"]

        if status == STATUS_SKIP:
            continue

        if status in (STATUS_LEFT, STATUS_RETIRED):
            last = last_by_player.get(pid)
            left_season = (next_season(last) if last else "") or label
            left_to = _text(row["Dokąd"]) if status == STATUS_LEFT else ""
            status_updates.append((pid, "left" if status == STATUS_LEFT else "retired", left_to or None, left_season))
            continue

        age, ovr = row["Wiek"], row["OVR"]
        if _blank(age) or _blank(ovr):
            errors.append(f"{name}: uzupełnij wiek i OVR (albo ustaw status „Pomiń”).")
            continue
        age, ovr = int(age), int(ovr)
        if not 14 <= age <= 50:
            errors.append(f"{name}: wiek musi być z zakresu 14-50.")
            continue
        if not 0 <= ovr <= 99:
            errors.append(f"{name}: OVR musi być z zakresu 0-99.")
            continue

        position = row["Poz."]
        if position not in POSITIONS:
            errors.append(f"{name}: wybierz pozycję.")
            continue
        if (position == "GK") != (current_positions.get(pid) == "GK"):
            errors.append(f"{name}: bramkarz musi zostać bramkarzem (a zawodnik z pola zawodnikiem z pola).")
            continue

        try:
            value = parse_money(row["Wartość (€)"])
        except ValueError:
            errors.append(f"{name}: wartość wpisz samymi cyframi, np. 3.000.000.")
            continue

        if label in labels_by_player.get(pid, set()):
            errors.append(f"{name}: ma już zapisany sezon {label}.")
            continue

        new_seasons.append((pid, label, position, age, ovr, value))

    if not errors and not new_seasons and not status_updates:
        errors.append("Nie ma nic do zapisania (wszystkie wiersze mają status „Pomiń”).")
    return new_seasons, status_updates, errors


# ---------- tabela końca sezonu ----------

def build_stats_table(rows) -> pd.DataFrame:
    columns = ["season_id", "Zawodnik", "Poz.", *STATS_COLUMNS]
    df = pd.DataFrame(
        [
            {
                "season_id": r["season_id"], "Zawodnik": r["shown_name"], "Poz.": r["position"],
                "Mecze": r["matches"], "Gole / CS": r["goals"], "Asysty": r["assists"],
            }
            for r in rows
        ],
        columns=columns,
    )
    if df.empty:
        return df
    df = _sorted_by_position(df, "Poz.", "Zawodnik").reset_index(drop=True)
    for column in STATS_COLUMNS:
        df[column] = df[column].fillna(0).astype(int)
    return df


def process_stats_table(edited: pd.DataFrame, original: pd.DataFrame) -> list:
    """Zwraca listę zmian (mecze, gole, asysty, id_sezonu) tylko dla wierszy, które się zmieniły."""
    changes = []
    for (_, new), (_, old) in zip(edited.iterrows(), original.iterrows()):
        values = [0 if _blank(new[c]) else max(0, int(new[c])) for c in STATS_COLUMNS]
        if values != [int(old[c]) for c in STATS_COLUMNS]:
            changes.append((*values, int(new["season_id"])))
    return changes


# ---------- widok ----------

def render_season_update() -> None:
    st.subheader("Aktualizacja sezonu")

    players = pd.DataFrame([dict(p) for p in get_players()])
    if players.empty:
        st.info("Najpierw dodaj zawodników.")
        return

    careers = (
        players[["game", "managed_club"]]
        .drop_duplicates()
        .sort_values(["game", "managed_club"], ascending=[False, True])
    )
    mapping = {f"FC {int(g)} · {club}": (int(g), club) for g, club in careers.itertuples(index=False)}
    choice = st.selectbox("Kariera", list(mapping), key="su_career")
    game, club = mapping[choice]

    mode = st.radio("Co aktualizujesz", [START_MODE, END_MODE], horizontal=True, key="su_mode")
    if mode == START_MODE:
        squad = players[(players["game"] == game) & (players["managed_club"] == club)]
        _render_start(squad, game, club)
    else:
        _render_end(game, club)


def _render_start(squad: pd.DataFrame, game: int, club: str) -> None:
    seasons = pd.DataFrame([dict(s) for s in get_all_seasons()])
    if not seasons.empty:
        seasons = seasons[seasons["player_id"].isin(squad["id"])]

    table, career_latest, last_by_player = build_start_table(squad, seasons)
    if table.empty:
        st.info("W tej karierze nie ma zawodników w kadrze (wszyscy mają status odejścia).")
        return

    labels_by_player = {}
    if not seasons.empty:
        labels_by_player = seasons.groupby("player_id")["season"].apply(set).to_dict()
    current_positions = squad.set_index("id")["position"].to_dict()

    st.caption(
        f"Ostatni sezon tej kariery: {career_latest or 'brak'}. Wiek, OVR, wartość i pozycja są skopiowane "
        "z poprzedniego sezonu (wiek +1), statystyki startują od zera. Zawodnikom, którzy odeszli, "
        "ustaw status „Odszedł” albo „Emerytura” (nie dostaną nowego sezonu)."
    )

    counter = st.session_state.setdefault("su_start_n", 0)
    key = f"{game}_{club}_{counter}"

    with st.form(f"su_start_form_{key}"):
        new_label = st.text_input(
            "Nowy sezon",
            value=next_season(career_latest) if career_latest else "",
            placeholder="2027/28 lub 2027",
            key=f"su_label_{key}",
        )
        edited = st.data_editor(
            table,
            key=f"su_editor_{key}",
            hide_index=True,
            num_rows="fixed",
            width="stretch",
            disabled=["Zawodnik", "Uwagi"],
            column_order=[c for c in START_COLUMNS if c != "id"],
            column_config={
                "id": None,
                "Zawodnik": st.column_config.TextColumn("Zawodnik"),
                "Status": st.column_config.SelectboxColumn(
                    "Status", options=STATUSES, required=True,
                    help="W kadrze: dostaje nowy sezon. Odszedł / Emerytura: bez nowego sezonu, zapisuje się odejście. Pomiń: bez zmian.",
                ),
                "Dokąd": st.column_config.TextColumn("Dokąd odszedł", help="Opcjonalnie: klub, do którego odszedł."),
                "Poz.": st.column_config.SelectboxColumn("Poz.", options=POSITIONS, required=True),
                "Wiek": st.column_config.NumberColumn("Wiek", min_value=14, max_value=50, step=1),
                "OVR": st.column_config.NumberColumn("OVR", min_value=0, max_value=99, step=1),
                "Wartość (€)": st.column_config.TextColumn("Wartość (€)", help="Np. 3.000.000"),
                "Uwagi": st.column_config.TextColumn("Uwagi"),
            },
        )
        saved = st.form_submit_button("Zapisz nowy sezon")

    if not saved:
        return

    new_seasons, status_updates, errors = process_start_table(
        edited, new_label, last_by_player, labels_by_player, current_positions
    )
    if errors:
        for error in errors:
            st.error(error)
        return

    try:
        apply_season_start(new_seasons, status_updates)
    except sqlite3.IntegrityError:
        st.error("Nie zapisano nic: któryś zawodnik ma już sezon o tej nazwie.")
        return

    parts = []
    if new_seasons:
        parts.append(f"nowy sezon {_text(new_label)} dla {len(new_seasons)} zawodników")
    if status_updates:
        parts.append(f"odejścia: {len(status_updates)}")
    st.session_state["flash"] = "Zapisano: " + ", ".join(parts) + "."
    st.session_state["su_start_n"] += 1
    st.rerun()


def _render_end(game: int, club: str) -> None:
    labels = get_career_seasons(game, club)
    if not labels:
        st.info("Ta kariera nie ma jeszcze żadnych sezonów. Najpierw zrób „Początek sezonu”.")
        return

    label = st.selectbox("Sezon", labels[::-1], key=f"su_end_season_{game}_{club}")
    original = build_stats_table(get_career_season_rows(game, club, label))

    st.caption(
        f"Wpisz statystyki sezonu {label}. Dla bramkarzy kolumna „Gole / CS” to czyste konta. "
        "Zapisują się tylko wiersze, które zmieniłeś."
    )

    counter = st.session_state.setdefault("su_end_n", 0)
    key = f"{game}_{club}_{label}_{counter}"

    with st.form(f"su_end_form_{key}"):
        edited = st.data_editor(
            original,
            key=f"su_stats_{key}",
            hide_index=True,
            num_rows="fixed",
            width="stretch",
            disabled=["Zawodnik", "Poz."],
            column_order=["Zawodnik", "Poz.", *STATS_COLUMNS],
            column_config={
                "season_id": None,
                "Mecze": st.column_config.NumberColumn("Mecze", min_value=0, step=1),
                "Gole / CS": st.column_config.NumberColumn("Gole / CS", min_value=0, step=1),
                "Asysty": st.column_config.NumberColumn("Asysty", min_value=0, step=1),
            },
        )
        saved = st.form_submit_button("Zapisz statystyki")

    if not saved:
        return

    changes = process_stats_table(edited, original)
    if not changes:
        st.info("Nic się nie zmieniło, więc nic nie zapisano.")
        return

    update_season_stats(changes)
    st.session_state["flash"] = f"Zapisano statystyki sezonu {label}: zmienione wiersze: {len(changes)}."
    st.session_state["su_end_n"] += 1
    st.rerun()