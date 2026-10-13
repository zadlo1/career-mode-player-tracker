import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "career.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    position      TEXT    NOT NULL,
    nationality   TEXT,
    game          INTEGER NOT NULL,
    managed_club  TEXT    NOT NULL,
    is_favorite   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS seasons (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id  INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    season     TEXT    NOT NULL,
    club       TEXT    NOT NULL,
    age        INTEGER,
    ovr        INTEGER,
    value_m    REAL,
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