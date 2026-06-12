"""SQLite 连接与 schema_final 初始化。"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "factory-balance.db"
SCHEMA_FILE = Path(__file__).resolve().parent / "schema_final.sql"
SCHEMA_VERSION = 1


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _schema_is_current(conn: sqlite3.Connection) -> bool:
    try:
        row = conn.execute("SELECT MAX(version) AS v FROM meta_schema").fetchone()
        return row is not None and row["v"] == SCHEMA_VERSION
    except sqlite3.OperationalError:
        return False


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
        if not _schema_is_current(conn):
            if DB_PATH.is_file():
                conn.close()
                DB_PATH.unlink()
                conn = get_connection()
            sql = SCHEMA_FILE.read_text(encoding="utf-8")
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO meta_schema (version, applied_at, note) VALUES (?, ?, ?)",
                (SCHEMA_VERSION, datetime.now(timezone.utc).isoformat(), "schema_final initial"),
            )
            conn.commit()
    finally:
        conn.close()
