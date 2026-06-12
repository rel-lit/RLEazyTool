"""模组指纹：小版本差异也会生成不同 pack。"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


def _read_mod_version(mods_dir: Path, mod_name: str) -> str | None:
    if not mods_dir.is_dir():
        return None
    prefix = f"{mod_name}_"
    for entry in mods_dir.iterdir():
        if not entry.is_dir():
            continue
        if entry.name == mod_name or entry.name.startswith(prefix):
            info = entry / "info.json"
            if info.is_file():
                try:
                    data = json.loads(info.read_text(encoding="utf-8"))
                    ver = data.get("version")
                    if ver:
                        return str(ver)
                except (OSError, json.JSONDecodeError):
                    pass
            if entry.name.startswith(prefix):
                return entry.name[len(prefix) :]
    return None


def read_enabled_mods_with_versions(mods_dir: Path) -> list[tuple[str, str | None]]:
    mod_list = mods_dir / "mod-list.json"
    names: list[str] = []
    if mod_list.is_file():
        try:
            data = json.loads(mod_list.read_text(encoding="utf-8"))
            for entry in data.get("mods") or []:
                if not isinstance(entry, dict) or not entry.get("enabled", True):
                    continue
                name = entry.get("name")
                if name and name != "factory-balance-sync":
                    names.append(str(name))
        except (OSError, json.JSONDecodeError):
            pass
    if not names:
        names = ["base"]
    pairs: list[tuple[str, str | None]] = []
    for name in sorted(set(names)):
        pairs.append((name, _read_mod_version(mods_dir, name)))
    return pairs


def compute_mod_fingerprint(mods_dir: Path) -> str:
    pairs = read_enabled_mods_with_versions(mods_dir)
    payload = [f"{n}@{v or '?'}" for n, v in pairs]
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode("utf-8")).hexdigest()
    return digest[:16]


def read_factorio_version_from_log(user_data: Path) -> str | None:
    for log_name in ("factorio-current.log", "factorio-previous.log"):
        log_path = user_data / log_name
        if not log_path.is_file():
            continue
        try:
            text = log_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = re.search(r"(?:Application version|Factorio version)[:\s]+(\d+\.\d+\.\d+(?:\.\d+)?)", text)
        if m:
            return m.group(1)
    return None
