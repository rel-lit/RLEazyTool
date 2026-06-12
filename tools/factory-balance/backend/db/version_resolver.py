"""Factorio 版本号解析（存档 / 日志统一口径）。"""

from __future__ import annotations

import re
from pathlib import Path

from core.factorio_paths import FactorioPaths, load_paths
from core.save_index import _read_save_version
from db.mod_fingerprint import read_factorio_version_from_log


def normalize_factorio_version(raw: str | None) -> str | None:
    if not raw:
        return None
    text = raw.strip()
    if not text or text.lower() == "unknown":
        return None
    m = re.match(r"^(\d+\.\d+\.\d+)", text)
    if m:
        return m.group(1)
    parts = text.split(".")
    if len(parts) >= 3 and parts[0].isdigit():
        return ".".join(parts[:3])
    return None


def resolve_factorio_version(
    save_path: Path | None = None,
    paths: FactorioPaths | None = None,
) -> str:
    paths = paths or load_paths()
    if save_path is not None:
        save_ver, _ = _read_save_version(save_path)
        normalized = normalize_factorio_version(save_ver)
        if normalized:
            return normalized
    log_ver = read_factorio_version_from_log(paths.user_data)
    normalized = normalize_factorio_version(log_ver)
    if normalized:
        return normalized
    return "unknown"
