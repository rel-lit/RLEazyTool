"""SQLite 连接与基于文件的 schema 迁移。"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "factory-balance.db"
SCHEMA_FILE = Path(__file__).resolve().parent / "schema_final.sql"
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
SCHEMA_VERSION = 6


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


def _discover_migrations() -> list[tuple[int, Path]]:
    """发现 migrations/ 目录下 NNN_description.sql 形式的脚本，按版本号排序。"""
    if not MIGRATIONS_DIR.is_dir():
        return []
    pattern = re.compile(r"^(\d{3})_.*\.sql$")
    migrations: list[tuple[int, Path]] = []
    for path in MIGRATIONS_DIR.iterdir():
        if not path.is_file():
            continue
        match = pattern.match(path.name)
        if match:
            migrations.append((int(match.group(1)), path))
    migrations.sort(key=lambda x: x[0])
    return migrations


def _apply_migrations(conn: sqlite3.Connection, from_version: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for version, path in _discover_migrations():
        if version <= from_version:
            continue
        sql = path.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO meta_schema (version, applied_at, note) VALUES (?, ?, ?)",
            (version, now, path.name),
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
