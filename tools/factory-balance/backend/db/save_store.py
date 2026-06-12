"""存档绑定与 recipe gate。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from db.catalog_builder import build_catalog
from db.connection import get_connection
from db.environment_store import touch_environment


def upsert_save_progress(
    *,
    save_key: str,
    save_path: Path,
    env_key: str,
    enabled_recipe_names: list[str],
    researched_tech_names: list[str],
    exported_tick: int | None,
    snapshot_id: int,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    try:
        mtime = save_path.stat().st_mtime
    except OSError:
        mtime = None

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO game_save (save_key, save_path, save_mtime, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(save_key) DO UPDATE SET
                save_path = excluded.save_path,
                save_mtime = excluded.save_mtime,
                updated_at = excluded.updated_at
            """,
            (save_key, str(save_path.resolve()), mtime, now, now),
        )

        name_to_id = {
            r["name"]: int(r["id"])
            for r in conn.execute(
                "SELECT id, name FROM snap_recipe WHERE snapshot_id = ?", (snapshot_id,)
            ).fetchall()
        }
        resolved_ids = [name_to_id[n] for n in enabled_recipe_names if n in name_to_id]

        conn.execute(
            """
            INSERT INTO save_binding (save_key, env_key, exported_tick, imported_at, enabled_count)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(save_key) DO UPDATE SET
                env_key = excluded.env_key,
                exported_tick = excluded.exported_tick,
                imported_at = excluded.imported_at,
                enabled_count = excluded.enabled_count
            """,
            (save_key, env_key, exported_tick, now, len(resolved_ids)),
        )
        conn.execute("DELETE FROM save_recipe_gate WHERE save_key = ?", (save_key,))
        conn.execute("DELETE FROM save_recipe_gate_name WHERE save_key = ?", (save_key,))
        conn.executemany(
            "INSERT INTO save_recipe_gate (save_key, recipe_id) VALUES (?, ?)",
            [(save_key, rid) for rid in resolved_ids],
        )
        conn.executemany(
            "INSERT INTO save_recipe_gate_name (save_key, recipe_name) VALUES (?, ?)",
            [(save_key, n) for n in enabled_recipe_names],
        )
        conn.commit()
    finally:
        conn.close()

    touch_environment(env_key)
    build_catalog(scope_kind="save", scope_key=save_key, env_key=env_key)


def get_save_binding(save_key: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM save_binding WHERE save_key = ?", (save_key,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_enabled_recipe_names(save_key: str) -> list[str]:
    conn = get_connection()
    try:
        return [
            r["recipe_name"]
            for r in conn.execute(
                "SELECT recipe_name FROM save_recipe_gate_name WHERE save_key = ? ORDER BY recipe_name",
                (save_key,),
            ).fetchall()
        ]
    finally:
        conn.close()


def load_cached_save(save_key: str, save_path: Path) -> bool:
    """若 DB 中已有且 mtime 未变，返回 True。"""
    return not is_save_progress_stale(save_key, save_path) and has_save_progress(save_key)


def has_save_progress(save_key: str) -> bool:
    return get_save_binding(save_key) is not None


def get_game_save_path(save_key: str) -> Path | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT save_path FROM game_save WHERE save_key = ?", (save_key,)
        ).fetchone()
        if not row or not row["save_path"]:
            return None
        return Path(row["save_path"])
    finally:
        conn.close()


def is_save_progress_stale(save_key: str, save_path: Path) -> bool:
    """存档文件 mtime 晚于上次导入则视为过期。"""
    if not has_save_progress(save_key):
        return False
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT save_mtime FROM game_save WHERE save_key = ?", (save_key,)
        ).fetchone()
        if not row or row["save_mtime"] is None:
            return False
        try:
            current = save_path.stat().st_mtime
            return current > float(row["save_mtime"]) + 1
        except OSError:
            return False
    finally:
        conn.close()


def get_save_progress_state(save_key: str, save_path: Path) -> dict[str, bool]:
    has_cache = has_save_progress(save_key)
    stale = has_cache and is_save_progress_stale(save_key, save_path)
    return {"has_cached_progress": has_cache, "needs_reimport": stale}


def active_progress_stale(active_save_key: str | None) -> bool:
    if not active_save_key:
        return False
    path = get_game_save_path(active_save_key)
    if path is None or not path.is_file():
        return False
    return is_save_progress_stale(active_save_key, path)
