"""存档列表与解析。"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .factorio_paths import FactorioPaths, load_paths, read_last_played_save_name


@dataclass
class SaveInfo:
    name: str
    path: str
    modified_at: str
    is_last_played: bool
    game_version: str | None = None
    mod_count: int | None = None


def _save_display_name(path: Path) -> str:
    if path.suffix.lower() == ".zip":
        return path.stem
    return path.name


def _read_save_version(save_path: Path) -> tuple[str | None, int | None]:
    if not zipfile.is_zipfile(save_path):
        return None, None
    try:
        with zipfile.ZipFile(save_path, "r") as zf:
            dat_name = next((n for n in zf.namelist() if n.endswith("level.dat")), None)
            if not dat_name:
                return None, None
            with zf.open(dat_name) as f:
                header = f.read(8)
            if len(header) >= 8:
                ver = ".".join(str(b) for b in header[4:8])
                return ver, None
    except (OSError, zipfile.BadZipFile, StopIteration):
        pass
    return None, None


def list_saves(paths: FactorioPaths | None = None) -> list[SaveInfo]:
    paths = paths or load_paths()
    last_name = read_last_played_save_name(paths.user_data)
    results: list[SaveInfo] = []

    if not paths.saves_dir.is_dir():
        return results

    for entry in paths.saves_dir.iterdir():
        if entry.is_file() and entry.suffix.lower() in {".zip", ".sav"}:
            mtime = datetime.fromtimestamp(entry.stat().st_mtime).isoformat(timespec="seconds")
            display = _save_display_name(entry)
            version, _ = _read_save_version(entry)
            results.append(
                SaveInfo(
                    name=display,
                    path=str(entry.resolve()),
                    modified_at=mtime,
                    is_last_played=display == last_name or entry.name == last_name,
                    game_version=version,
                )
            )

    results.sort(key=lambda s: s.modified_at, reverse=True)
    return results


def resolve_save_path(name_or_path: str, paths: FactorioPaths | None = None) -> Path | None:
    paths = paths or load_paths()
    candidate = Path(name_or_path)
    if candidate.is_file():
        return candidate.resolve()

    if paths.saves_dir.is_dir():
        for entry in paths.saves_dir.iterdir():
            if _save_display_name(entry) == name_or_path or entry.name == name_or_path:
                return entry.resolve()
            if entry.stem == name_or_path:
                return entry.resolve()
    return None
