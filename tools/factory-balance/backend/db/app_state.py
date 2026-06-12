"""app_state 与缓存清理。"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from db.connection import DB_PATH, get_connection


def get_active_save_key() -> str | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT active_save_key FROM app_state WHERE id = 1").fetchone()
        return str(row["active_save_key"]) if row and row["active_save_key"] else None
    finally:
        conn.close()


def set_active_save_key(save_key: str | None) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE app_state SET active_save_key = ?, updated_at = ? WHERE id = 1
            """,
            (save_key, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def get_catalog_scope() -> str:
    conn = get_connection()
    try:
        row = conn.execute("SELECT catalog_scope FROM app_state WHERE id = 1").fetchone()
        return str(row["catalog_scope"]) if row else "save"
    finally:
        conn.close()


def set_catalog_scope(scope: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE app_state SET catalog_scope = ?, updated_at = ? WHERE id = 1",
            (scope, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def purge_stale(*, keep_active: bool = True) -> dict:
    conn = get_connection()
    deleted_env = 0
    deleted_saves = 0
    try:
        active = get_active_save_key() if keep_active else None

        if keep_active and active:
            cur = conn.execute("DELETE FROM game_save WHERE save_key != ?", (active,))
            deleted_saves = cur.rowcount
        elif not keep_active:
            cur = conn.execute("DELETE FROM game_save")
            deleted_saves = cur.rowcount
            conn.execute("UPDATE app_state SET active_save_key = NULL WHERE id = 1")

        referenced_envs = {
            r["env_key"]
            for r in conn.execute("SELECT DISTINCT env_key FROM save_binding").fetchall()
        }
        if active:
            row = conn.execute("SELECT env_key FROM save_binding WHERE save_key = ?", (active,)).fetchone()
            if row:
                referenced_envs.add(row["env_key"])

        for row in conn.execute("SELECT env_key FROM game_environment").fetchall():
            ek = row["env_key"]
            if ek in referenced_envs:
                continue
            conn.execute("DELETE FROM game_environment WHERE env_key = ?", (ek,))
            deleted_env += 1

        orphan_snapshots = conn.execute(
            """
            SELECT s.id, s.source_path FROM game_snapshot s
            WHERE NOT EXISTS (SELECT 1 FROM game_environment e WHERE e.snapshot_id = s.id)
            """
        ).fetchall()
        for snap in orphan_snapshots:
            conn.execute("DELETE FROM game_snapshot WHERE id = ?", (int(snap["id"]),))
            sp = snap["source_path"]
            if sp:
                p = Path(sp).parent
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)

        conn.commit()
    finally:
        conn.close()

    legacy: list[str] = []
    cache = DB_PATH.parent / "cache"
    for name in ("session-state.json", "progress-cache.json"):
        p = cache / name
        if p.is_file():
            p.unlink()
            legacy.append(name)

    return {"deleted_environments": deleted_env, "deleted_saves": deleted_saves, "legacy_files_removed": legacy}
