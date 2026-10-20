import pandas as pd
import streamlit as st

from db import get_all_seasons, get_players
from ui import format_money, ranking_table_html

TOP_N = 10


def _matches_text(n: int) -> str:
    if n == 1:
        return "1 mecz"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return f"{n} mecze"
    return f"{n} meczów"


def _load(game_filter, club_filter, fav_only, type_filter):
    players = pd.DataFrame([dict(p) for p in get_players()])
    if players.empty:
        return players, pd.DataFrame()

    if game_filter is not None:
        players = players[players["game"] == game_filter]
    if club_filter is not None:
        players = players[players["managed_club"] == club_filter]
    if fav_only:
        players = players[players["is_favorite"] == 1]
    if type_filter == "Prawdziwi":
        players = players[players["is_generated"] == 0]
    elif type_filter == "Wygenerowani przez grę":
        players = players[players["is_generated"] == 1]

    seasons = pd.DataFrame([dict(s) for s in get_all_seasons()])
    if seasons.empty:
        return players, seasons
    return players, seasons[seasons["player_id"].isin(players["id"])]


def _totals(players: pd.DataFrame, seasons: pd.DataFrame, column: str) -> pd.DataFrame:
    totals = (
        seasons.groupby("player_id")
        .agg(total=(column, "sum"), games=("matches", "sum"))
        .reset_index()
    )
    return players.merge(totals, left_on="id", right_on="player_id")


def _count_ranking(players: pd.DataFrame, seasons: pd.DataFrame, column: str) -> pd.DataFrame:
    df = _totals(players, seasons, column)
    df = df[df["total"] > 0]
    if df.empty:
        return df
    df = df.sort_values(["total", "shown_name"], ascending=[False, True]).head(TOP_N).copy()
    df["value_text"] = df["total"].astype(int).astype(str)
    df["detail_text"] = df["games"].astype(int).map(_matches_text)
    return df


def _scorers(players, seasons):
    return _count_ranking(players[players["position"] != "GK"], seasons, "goals")


def _clean_sheets(players, seasons):
    return _count_ranking(players[players["position"] == "GK"], seasons, "goals")


def _assists(players, seasons):
    return _count_ranking(players, seasons, "assists")


def _most_valuable(players: pd.DataFrame, seasons: pd.DataFrame) -> pd.DataFrame:
    with_value = seasons.dropna(subset=["value_eur"])
    if with_value.empty:
        return pd.DataFrame()

    idx = with_value.groupby("player_id")["value_eur"].idxmax()
    best = with_value.loc[idx, ["player_id", "season", "age", "ovr", "value_eur"]].rename(
        columns={"season": "best_season", "age": "best_age", "ovr": "best_ovr", "value_eur": "best_value"}
    )
    df = players.merge(best, left_on="id", right_on="player_id")
    if df.empty:
        return df
    df = df.sort_values(["best_value", "shown_name"], ascending=[False, True]).head(TOP_N).copy()

    def describe(r) -> str:
        parts = [f"sezon {r['best_season']}"]
        if pd.notna(r["best_age"]):
            parts.append(f"wiek {int(r['best_age'])}")
        if pd.notna(r["best_ovr"]):
            parts.append(f"OVR {int(r['best_ovr'])}")
        return ", ".join(parts)

    df["value_text"] = df["best_value"].map(format_money)
    df["detail_text"] = df.apply(describe, axis=1)
    return df


def _growth(players: pd.DataFrame, seasons: pd.DataFrame) -> pd.DataFrame:
    rated = seasons.dropna(subset=["ovr"]).sort_values(["player_id", "season"])
    if rated.empty:
        return pd.DataFrame()

    grouped = rated.groupby("player_id")
    result = pd.DataFrame(
        {
            "first_season": grouped["season"].first(),
            "first_ovr": grouped["ovr"].first(),
            "last_season": grouped["season"].last(),
            "last_ovr": grouped["ovr"].last(),
            "n": grouped.size(),
        }
    ).reset_index()
    result = result[result["n"] >= 2].copy()
    result["gain"] = result["last_ovr"] - result["first_ovr"]
    result = result[result["gain"] > 0]

    df = players.merge(result, left_on="id", right_on="player_id")
    if df.empty:
        return df
    df = df.sort_values(["gain", "shown_name"], ascending=[False, True]).head(TOP_N).copy()
    df["value_text"] = df["gain"].astype(int).map(lambda g: f"+{g}")
    df["detail_text"] = df.apply(
        lambda r: f"{int(r['first_ovr'])} → {int(r['last_ovr'])} ({r['first_season']} → {r['last_season']})",
        axis=1,
    )
    return df


def render_rankings(game_filter, club_filter, fav_only, type_filter) -> None:
    st.subheader("Rankingi")

    active = []
    if game_filter is not None:
        active.append(f"gra FC {game_filter}")
    if club_filter is not None:
        active.append(f"klub {club_filter}")
    if fav_only:
        active.append("tylko ulubieni")
    if type_filter != "Wszyscy":
        active.append(type_filter.lower())
    st.caption(
        "Uwzględnione filtry: " + (", ".join(active) if active else "brak (wszyscy zawodnicy)")
        + f". Pokazuję top {TOP_N}."
    )

    players, seasons = _load(game_filter, club_filter, fav_only, type_filter)
    if players.empty or seasons.empty:
        st.info("Brak danych do rankingów. Dodaj zawodników i ich sezony.")
        return

    rankings = [
        ("Strzelcy", _scorers(players, seasons), "Gole", "Mecze"),
        ("Czyste konta", _clean_sheets(players, seasons), "Czyste konta", "Mecze"),
        ("Asysty", _assists(players, seasons), "Asysty", "Mecze"),
        ("Najdroższy", _most_valuable(players, seasons), "Najwyższa wartość", "Kiedy"),
        ("Największy rozwój", _growth(players, seasons), "Zmiana OVR", "Przebieg"),
    ]

    tabs = st.tabs([name for name, *_ in rankings])
    for tab, (_, df, value_header, detail_header) in zip(tabs, rankings):
        with tab:
            if df.empty:
                st.info("Brak danych w tym rankingu.")
            else:
                st.html(ranking_table_html(df, value_header, detail_header))