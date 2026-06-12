"""SQLite 连接与 schema_final 初始化。"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "factory-balance.db"
SCHEMA_FILE = Path(__file__).resolve().parent / "schema_final.sql"
SCHEMA_VERSION = 4

_MIGRATION_V4 = """
CREATE TABLE IF NOT EXISTS layout_compute_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    save_key        TEXT,
    env_key         TEXT,
    catalog_mode    TEXT NOT NULL DEFAULT 'progress',
    supply_mode     TEXT NOT NULL DEFAULT 'raw',
    target_summary  TEXT NOT NULL,
    target_count    INTEGER NOT NULL DEFAULT 0,
    node_count      INTEGER NOT NULL DEFAULT 0,
    edge_count      INTEGER NOT NULL DEFAULT 0,
    tap_count       INTEGER NOT NULL DEFAULT 0,
    request_json    TEXT NOT NULL,
    response_json   TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_layout_history_created ON layout_compute_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_layout_history_save ON layout_compute_history(save_key);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _current_schema_version(conn: sqlite3.Connection) -> int:
    try:
        row = conn.execute("SELECT MAX(version) AS v FROM meta_schema").fetchone()
        return int(row["v"]) if row and row["v"] is not None else 0
    except sqlite3.OperationalError:
        return 0


def _apply_migrations(conn: sqlite3.Connection, from_version: int) -> None:
    if from_version < 4:
        conn.executescript(_MIGRATION_V4)
        conn.execute(
            "INSERT INTO meta_schema (version, applied_at, note) VALUES (?, ?, ?)",
            (
                4,
                datetime.now(timezone.utc).isoformat(),
                "layout_compute_history table",
            ),
        )


def init_db(*, reset: bool = False) -> None:
    if reset and DB_PATH.is_file():
        DB_PATH.unlink()
        wal = DB_PATH.with_suffix(".db-wal")
        shm = DB_PATH.with_suffix(".db-shm")
        for p in (wal, shm):
            if p.is_file():
                p.unlink()

    conn = get_connection()
    try:
        current = _current_schema_version(conn)
        if current == 0:
            sql = SCHEMA_FILE.read_text(encoding="utf-8")
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO meta_schema (version, applied_at, note) VALUES (?, ?, ?)",
                (SCHEMA_VERSION, datetime.now(timezone.utc).isoformat(), "schema_final initial"),
            )
            conn.commit()
        elif current < SCHEMA_VERSION:
            _apply_migrations(conn, current)
            conn.commit()
        elif current > SCHEMA_VERSION:
            pass
    finally:
        conn.close()
