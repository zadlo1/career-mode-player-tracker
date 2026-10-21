import sqlite3
from pathlib import Path

from countries import COUNTRIES, NAME_TO_CODE

DB_PATH = Path(__file__).parent / "data" / "career.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    display_name  TEXT,
    position      TEXT    NOT NULL,
    nationality   TEXT,
    game          INTEGER NOT NULL,
    managed_club  TEXT    NOT NULL,
    original_club TEXT,
    is_favorite   INTEGER NOT NULL DEFAULT 0,
    is_generated  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS seasons (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id  INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    season     TEXT    NOT NULL,
    position   TEXT,
    age        INTEGER,
    ovr        INTEGER,
    value_eur  INTEGER,
    matches    INTEGER NOT NULL DEFAULT 0,
    goals      INTEGER NOT NULL DEFAULT 0,
    assists    INTEGER NOT NULL DEFAULT 0,
    UNIQUE (player_id, season)
);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        _migrate_season_position(conn)
        _migrate_player_generated(conn)
        _migrate_nationalities(conn)


def _migrate_season_position(conn: sqlite3.Connection) -> None:
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(seasons)").fetchall()]
    if "position" not in columns:
        conn.execute("ALTER TABLE seasons ADD COLUMN position TEXT")
        conn.execute(
            """
            UPDATE seasons
            SET position = (SELECT p.position FROM players p WHERE p.id = seasons.player_id)
            WHERE position IS NULL
            """
        )


def _migrate_player_generated(conn: sqlite3.Connection) -> None:
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(players)").fetchall()]
    if "is_generated" not in columns:
        conn.execute("ALTER TABLE players ADD COLUMN is_generated INTEGER NOT NULL DEFAULT 0")


def _migrate_nationalities(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT DISTINCT nationality FROM players
        WHERE nationality IS NOT NULL AND TRIM(nationality) != ''
        """
    ).fetchall()
    for row in rows:
        value = row["nationality"]
        if value in COUNTRIES:
            continue
        code = NAME_TO_CODE.get(value.strip().lower())
        if code:
            conn.execute(
                "UPDATE players SET nationality = ? WHERE nationality = ?",
                (code, value),
            )


def add_player(name, display_name, position, nationality, game, managed_club,
               original_club, is_generated=False) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO players (name, display_name, position, nationality, game,
                                 managed_club, original_club, is_generated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, display_name, position, nationality, game, managed_club,
             original_club, 1 if is_generated else 0),
        )
        return cur.lastrowid


def get_players() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT p.id, p.name,
                   COALESCE(NULLIF(TRIM(p.display_name), ''), p.name) AS shown_name,
                   p.display_name,
                   COALESCE(NULLIF(TRIM(ls.position), ''), p.position) AS position,
                   p.position AS start_position,
                   p.nationality, p.game, p.managed_club, p.original_club, p.is_favorite,
                   p.is_generated,
                   ls.age, ls.ovr, ls.value_eur,
                   agg.max_ovr, agg.max_value, agg.matches, agg.goals, agg.assists
            FROM players p
            LEFT JOIN seasons ls ON ls.id = (
                SELECT s.id FROM seasons s
                WHERE s.player_id = p.id
                ORDER BY s.season DESC
                LIMIT 1
            )
            LEFT JOIN (
                SELECT player_id,
                       MAX(ovr) AS max_ovr,
                       MAX(value_eur) AS max_value,
                       SUM(matches) AS matches,
                       SUM(goals) AS goals,
                       SUM(assists) AS assists
                FROM seasons
                GROUP BY player_id
            ) agg ON agg.player_id = p.id
            ORDER BY shown_name
            """
        ).fetchall()


def add_season(player_id, season, position, age, ovr, value_eur, matches, goals, assists) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO seasons (player_id, season, position, age, ovr, value_eur, matches, goals, assists)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (player_id, season, position, age, ovr, value_eur, matches, goals, assists),
        )


def get_seasons(player_id) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, season, position, age, ovr, value_eur, matches, goals, assists
            FROM seasons
            WHERE player_id = ?
            ORDER BY season
            """,
            (player_id,),
        ).fetchall()


def get_all_seasons() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT player_id, season, position, age, ovr, value_eur, matches, goals, assists
            FROM seasons
            ORDER BY player_id, season
            """
        ).fetchall()


def get_games() -> list[int]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT game FROM players ORDER BY game DESC"
        ).fetchall()
        return [r["game"] for r in rows]


def get_clubs() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT managed_club FROM players ORDER BY managed_club"
        ).fetchall()
        return [r["managed_club"] for r in rows]


def get_all_clubs() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT managed_club AS club FROM players
            UNION
            SELECT original_club FROM players
            WHERE original_club IS NOT NULL AND TRIM(original_club) != ''
            ORDER BY club
            """
        ).fetchall()
        return [r["club"] for r in rows]


def set_favorite(player_id, value) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE players SET is_favorite = ? WHERE id = ?",
            (1 if value else 0, player_id),
        )


def update_player(player_id, name, display_name, position, nationality,
                  game, managed_club, original_club, is_generated=False) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE players
            SET name = ?, display_name = ?, position = ?, nationality = ?,
                game = ?, managed_club = ?, original_club = ?, is_generated = ?
            WHERE id = ?
            """,
            (name, display_name, position, nationality, game, managed_club,
             original_club, 1 if is_generated else 0, player_id),
        )


def delete_player(player_id) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM players WHERE id = ?", (player_id,))


def update_season(season_id, season, position, age, ovr, value_eur, matches, goals, assists) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE seasons
            SET season = ?, position = ?, age = ?, ovr = ?, value_eur = ?,
                matches = ?, goals = ?, assists = ?
            WHERE id = ?
            """,
            (season, position, age, ovr, value_eur, matches, goals, assists, season_id),
        )


def delete_season(season_id) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM seasons WHERE id = ?", (season_id,))