"""game_environment 读写。"""

from __future__ import annotations

from datetime import datetime, timezone

from core.factorio_paths import FactorioPaths, load_paths
from core.locale_loader import read_game_locale
from db.connection import get_connection
from db.mod_fingerprint import compute_mod_fingerprint, read_enabled_mods_with_versions
from db.version_resolver import resolve_factorio_version


def make_env_key(factorio_version: str, mod_fingerprint: str, locale: str) -> str:
    return f"{factorio_version}__{mod_fingerprint}__{locale}"


def find_environment(factorio_version: str, mod_fingerprint: str, locale: str) -> str | None:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT env_key FROM game_environment
            WHERE factorio_version = ? AND mod_fingerprint = ? AND locale = ?
            """,
            (factorio_version, mod_fingerprint, locale),
        ).fetchone()
        return str(row["env_key"]) if row else None
    finally:
        conn.close()


def get_environment(env_key: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM game_environment WHERE env_key = ?", (env_key,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def register_environment(
    *,
    snapshot_id: int,
    factorio_version: str,
    mod_fingerprint: str,
    locale: str,
    mods: list[tuple[str, str | None]] | None = None,
    label: str | None = None,
) -> str:
    env_key = make_env_key(factorio_version, mod_fingerprint, locale)
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT env_key FROM game_environment WHERE env_key = ?", (env_key,)
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE game_environment SET snapshot_id = ?, label = ?, last_used_at = ?
                WHERE env_key = ?
                """,
                (snapshot_id, label, now, env_key),
            )
            conn.execute("DELETE FROM environment_mod WHERE env_key = ?", (env_key,))
        else:
            conn.execute(
                """
                INSERT INTO game_environment
                (env_key, factorio_version, mod_fingerprint, locale, snapshot_id, label, last_used_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (env_key, factorio_version, mod_fingerprint, locale, snapshot_id, label, now, now),
            )

        if mods:
            for i, (mod_name, mod_version) in enumerate(mods):
                conn.execute(
                    """
                    INSERT INTO environment_mod (env_key, mod_name, mod_version, sort_ord)
                    VALUES (?, ?, ?, ?)
                    """,
                    (env_key, mod_name, mod_version, i),
                )
        conn.commit()
        return env_key
    finally:
        conn.close()


def touch_environment(env_key: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE game_environment SET last_used_at = ? WHERE env_key = ?",
            (datetime.now(timezone.utc).isoformat(), env_key),
        )
        conn.commit()
    finally:
        conn.close()


def has_any_environment() -> bool:
    conn = get_connection()
    try:
        row = conn.execute("SELECT 1 FROM game_environment LIMIT 1").fetchone()
        return row is not None
    finally:
        conn.close()


def list_environments() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT env_key, factorio_version, mod_fingerprint, locale, label, last_used_at, snapshot_id
            FROM game_environment ORDER BY last_used_at DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def resolve_current_environment(
    paths: FactorioPaths | None = None,
    *,
    save_path=None,
) -> tuple[str, str, str, list[tuple[str, str | None]]]:
    paths = paths or load_paths()
    locale = read_game_locale(paths.config_file)
    mod_fp = compute_mod_fingerprint(paths.mods_dir)
    version = resolve_factorio_version(save_path, paths)
    mods = read_enabled_mods_with_versions(paths.mods_dir)
    env_key = make_env_key(version, mod_fp, locale)
    return env_key, version, mod_fp, mods
