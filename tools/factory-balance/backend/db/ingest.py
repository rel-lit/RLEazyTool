"""导入编排：dump → snapshot → environment → catalog。"""

from __future__ import annotations

from pathlib import Path

from core.factorio_paths import FactorioPaths, load_paths
from core.locale_loader import read_game_locale
from core.prototype_loader import run_prototype_dump
from db.catalog_builder import build_catalog
from db.environment_store import (
    find_environment,
    register_environment,
    resolve_current_environment,
    touch_environment,
)
from db.mod_fingerprint import read_enabled_mods_with_versions
from db.snapshot_etl import find_snapshot_by_sha, ingest_dump_file
from db.version_resolver import resolve_factorio_version


def _display_label(factorio_version: str, mods: list[tuple[str, str | None]]) -> str:
    names = [m[0] for m in mods if m[0] != "factory-balance-sync"]
    mod_part = "+".join(names[:3])
    if len(names) > 3:
        mod_part += "…"
    return f"{factorio_version} · {mod_part or 'vanilla'}"


def ingest_snapshot_from_dump(
    paths: FactorioPaths | None = None,
    *,
    save_path: Path | None = None,
) -> tuple[str, list[str]]:
    """Factorio dump + ETL + environment + environment catalog。返回 (env_key, warnings)。"""
    paths = paths or load_paths()
    warnings: list[str] = []

    env_key, factorio_version, mod_fp, mods = resolve_current_environment(paths, save_path=save_path)
    locale = read_game_locale(paths.config_file)
    mod_names = [m[0] for m in mods]

    existing_env = find_environment(factorio_version, mod_fp, locale)
    if existing_env:
        warnings.append(f"环境已存在 ({existing_env})，将刷新 dump 绑定。")

    dump_path, _, dump_warnings = run_prototype_dump(paths)
    warnings.extend(dump_warnings)

    snapshot_id, content_sha = ingest_dump_file(dump_path, locale=locale, mod_names=mod_names)
    if find_snapshot_by_sha(content_sha) != snapshot_id:
        pass

    label = _display_label(factorio_version, mods)
    env_key = register_environment(
        snapshot_id=snapshot_id,
        factorio_version=factorio_version,
        mod_fingerprint=mod_fp,
        locale=locale,
        mods=mods,
        label=label,
    )
    touch_environment(env_key)
    build_catalog(scope_kind="environment", scope_key=env_key, env_key=env_key)
    warnings.append(f"已入库环境 {env_key}（snapshot={content_sha[:12]}…）")
    return env_key, warnings


def ensure_environment(
    paths: FactorioPaths | None = None,
    *,
    save_path: Path | None = None,
) -> tuple[str, list[str]]:
    paths = paths or load_paths()
    locale = read_game_locale(paths.config_file)
    factorio_version = resolve_factorio_version(save_path, paths)
    from db.mod_fingerprint import compute_mod_fingerprint

    mod_fp = compute_mod_fingerprint(paths.mods_dir)
    existing = find_environment(factorio_version, mod_fp, locale)
    if existing:
        touch_environment(existing)
        from db.catalog_query import ensure_build_exists

        ensure_build_exists("environment", existing, existing)
        return existing, []

    warnings = [
        f"未找到环境 ({factorio_version}, {mod_fp[:8]}…)，正在启动 Factorio 导入全配方（约 1–3 分钟）…"
    ]
    env_key, ingest_warnings = ingest_snapshot_from_dump(paths, save_path=save_path)
    warnings.extend(ingest_warnings)
    return env_key, warnings


def get_snapshot_id_for_env(env_key: str) -> int:
    from db.environment_store import get_environment

    env = get_environment(env_key)
    if not env:
        raise ValueError(env_key)
    return int(env["snapshot_id"])
