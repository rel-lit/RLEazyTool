"""从 Factorio 安装目录 locale/*.cfg 读取本地化名称。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .factorio_paths import FactorioPaths, load_paths

SECTION_TO_KIND = {
    "item-name": "item",
    "fluid-name": "fluid",
    "recipe-name": "recipe",
    "entity-name": "entity",
    "equipment-name": "equipment",
    "technology-name": "technology",
    "tool-name": "tool",
    "armor-name": "armor",
    "module-name": "module",
    "ammo-name": "ammo",
    "capsule-name": "capsule",
    "gun-name": "gun",
}

DEFAULT_LOCALE = "zh-CN"
SKIP_MODS = {"factory-balance-sync"}
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
LOCALE_FILE = CACHE_DIR / "prototype-locale.json"


def resolve_game_data_dir(executable: Path) -> Path:
    """Factorio.exe 位于 bin/x64/，数据目录为安装根下的 data/。"""
    install_root = executable.resolve().parent.parent.parent
    data_dir = install_root / "data"
    if data_dir.is_dir():
        return data_dir
    raise FileNotFoundError(f"未找到 Factorio data 目录: {data_dir}")


def read_enabled_mod_names(mods_dir: Path) -> list[str]:
    mod_list = mods_dir / "mod-list.json"
    if not mod_list.is_file():
        return ["base"]
    try:
        data = json.loads(mod_list.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["base"]
    names: list[str] = []
    for entry in data.get("mods") or []:
        if not isinstance(entry, dict):
            continue
        if not entry.get("enabled", True):
            continue
        name = entry.get("name")
        if name and name not in SKIP_MODS:
            names.append(str(name))
    return names or ["base"]


def read_game_locale(config_file: Path | None) -> str:
    if config_file and config_file.is_file():
        for line in config_file.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("locale="):
                val = line.split("=", 1)[1].strip()
                if val and val != "auto":
                    return val
    return DEFAULT_LOCALE


def _locale_cfg_paths(data_dir: Path, mod_names: list[str], locale: str) -> list[Path]:
    paths: list[Path] = []
    core_cfg = data_dir / "core" / "locale" / locale / "core.cfg"
    if core_cfg.is_file():
        paths.append(core_cfg)

    seen: set[Path] = set()
    for mod in mod_names:
        if mod in SKIP_MODS:
            continue
        loc_dir = data_dir / mod / "locale" / locale
        if not loc_dir.is_dir():
            continue
        preferred = loc_dir / f"{mod}.cfg"
        if preferred.is_file():
            if preferred not in seen:
                paths.append(preferred)
                seen.add(preferred)
            continue
        for cfg in sorted(loc_dir.glob("*.cfg")):
            if cfg not in seen:
                paths.append(cfg)
                seen.add(cfg)
    return paths


def parse_factorio_cfg(path: Path) -> dict[str, dict[str, str]]:
    tables: dict[str, dict[str, str]] = {}
    section: str | None = None
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return tables

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            continue
        if section not in SECTION_TO_KIND or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not key or not value:
            continue
        kind = SECTION_TO_KIND[section]
        tables.setdefault(kind, {})[key] = value
    return tables


def _to_locale_tables(parsed: dict[str, dict[str, str]]) -> dict[str, dict[str, dict[str, list[str]]]]:
    locale: dict[str, dict[str, dict[str, list[str]]]] = {}
    for kind, names in parsed.items():
        bucket = locale.setdefault(kind, {})
        for name, label in names.items():
            bucket[name] = {"localised_name": [label]}
    return locale


def merge_locale_tables(*chunks: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for chunk in chunks:
        for kind, table in chunk.items():
            if not isinstance(table, dict):
                continue
            merged.setdefault(kind, {}).update(table)
    return merged


def locale_has_names(locale: dict[str, Any], *, min_items: int = 50) -> bool:
    items = locale.get("item")
    if isinstance(items, dict) and len(items) >= min_items:
        return True
    return False


def load_locale_from_install(
    paths: FactorioPaths | None = None,
    *,
    locale: str | None = None,
    mod_names: list[str] | None = None,
) -> dict[str, Any]:
    paths = paths or load_paths()
    if paths.executable is None:
        return {}

    try:
        data_dir = resolve_game_data_dir(paths.executable)
    except FileNotFoundError:
        return {}

    lang = locale or read_game_locale(paths.config_file)
    mods = mod_names or read_enabled_mod_names(paths.mods_dir)

    parsed: dict[str, dict[str, str]] = {}
    for cfg_path in _locale_cfg_paths(data_dir, mods, lang):
        chunk = parse_factorio_cfg(cfg_path)
        for kind, table in chunk.items():
            parsed.setdefault(kind, {}).update(table)

    return _to_locale_tables(parsed)


def ensure_locale_cache(
    paths: FactorioPaths | None = None,
    cache_file: Path | None = None,
    *,
    mod_names: list[str] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """合并 JSON 缓存与安装目录 cfg，必要时写回 cache。"""
    paths = paths or load_paths()
    cache_file = cache_file or LOCALE_FILE
    warnings: list[str] = []

    merged: dict[str, Any] = {}
    if cache_file.is_file():
        try:
            merged = json.loads(cache_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            merged = {}

    for extra in (CACHE_DIR / "item-locale.json", CACHE_DIR / "recipe-locale.json"):
        if extra.is_file():
            try:
                chunk = json.loads(extra.read_text(encoding="utf-8"))
                merged = merge_locale_tables(merged, chunk)
            except (OSError, json.JSONDecodeError):
                pass

    install_locale = load_locale_from_install(paths, mod_names=mod_names)
    if install_locale:
        merged = merge_locale_tables(merged, install_locale)
        if not locale_has_names(install_locale):
            warnings.append("已从游戏 locale 读取部分名称，但条目较少，请确认语言包完整。")
    elif not locale_has_names(merged):
        warnings.append(
            "未找到中文 locale（Factorio 2.0 不再单独导出 locale 文件）。"
            "请确认已安装 Factorio 且 mod-list.json 可读。"
        )

    if locale_has_names(merged):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            cache_file.write_text(json.dumps(merged, ensure_ascii=False), encoding="utf-8")
        except OSError:
            warnings.append("locale 缓存写入失败，本次会话仍可使用内存中的名称。")

    return merged, warnings
