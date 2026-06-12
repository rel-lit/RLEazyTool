"""存档进度与会话状态本地缓存。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from .progress_snapshot import ProgressSnapshot
from models.game_data import GameVersionKey, SaveProgressRecord

if TYPE_CHECKING:
    from .game_session import GameSession

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
PROGRESS_CACHE_FILE = CACHE_DIR / "progress-cache.json"
SESSION_STATE_FILE = CACHE_DIR / "session-state.json"


def is_internal_item(name: str) -> bool:
    return name.startswith("parameter-")


def filter_player_items(names: list[str] | set[str]) -> list[str]:
    return sorted({n for n in names if n and not is_internal_item(n)})


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def save_progress_cache(
    save_path: Path,
    snapshot: ProgressSnapshot,
    *,
    version_key: GameVersionKey | None = None,
) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        save_mtime = save_path.stat().st_mtime
    except OSError:
        save_mtime = 0.0
    record = SaveProgressRecord(
        version_key=version_key,
        source_save=str(save_path.resolve()),
        save_mtime=save_mtime,
        researched_technologies=snapshot.researched_technologies,
        enabled_recipes=snapshot.enabled_recipes,
        mod_names=snapshot.mod_names,
        exported_at_tick=snapshot.exported_at,
        cached_at=datetime.now(timezone.utc).isoformat(),
    )
    payload = {"save_path": record.source_save, "save_mtime": save_mtime, "progress": record.to_dict()}
    PROGRESS_CACHE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_progress_cache(save_path: Path) -> tuple[ProgressSnapshot | None, list[str]]:
    warnings: list[str] = []
    data = _read_json(PROGRESS_CACHE_FILE)
    if not data:
        return None, warnings

    cached_save = str(data.get("save_path") or "")
    if not cached_save or Path(cached_save).resolve() != save_path.resolve():
        return None, warnings

    try:
        current_mtime = save_path.stat().st_mtime
        cached_mtime = float(data.get("save_mtime") or 0)
    except OSError:
        return None, warnings

    if current_mtime > cached_mtime + 1:
        warnings.append("存档文件已更新，缓存可能过期；请重新「从存档导入」。")

    progress = data.get("progress")
    if not isinstance(progress, dict):
        return None, warnings

    record = SaveProgressRecord.from_dict({**progress, "source_save": str(save_path.resolve())})

    if record.version_key:
        from .version_registry import has_pack

        if not has_pack(record.version_key):
            warnings.append(
                f"存档对应配方包 {record.version_key.pack_slug()} 尚未生成，请点「完整全配方」。"
            )

    snapshot = ProgressSnapshot(
        researched_technologies=record.researched_technologies,
        enabled_recipes=record.enabled_recipes,
        craftable_items=[],
        mod_names=record.mod_names,
        source_save=record.source_save,
        exported_at=record.exported_at_tick,
    )
    cached_at = data.get("cached_at")
    if cached_at:
        warnings.append(f"已从本地缓存加载进度（{cached_at}，未启动 Factorio）。")
    else:
        warnings.append("已从本地缓存加载进度（未启动 Factorio）。")
    return snapshot, warnings


def save_session_state(session: GameSession) -> None:
    if session.progress is None:
        return
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": session.updated_at,
        "database_source": session.database_source,
        "warnings": session.warnings,
        "progress": {
            "researched_technologies": session.progress.researched_technologies,
            "enabled_recipes": session.progress.enabled_recipes,
            "craftable_items": sorted(session.craftable_items),
            "mod_names": session.progress.mod_names,
            "source_save": session.progress.source_save,
            "exported_at": session.progress.exported_at,
        },
    }
    SESSION_STATE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def restore_session_from_cache() -> bool:
    from .game_session import SESSION

    data = _read_json(SESSION_STATE_FILE)
    if not data:
        return False
    progress = data.get("progress")
    if not isinstance(progress, dict):
        return False

    snapshot = ProgressSnapshot(
        researched_technologies=list(progress.get("researched_technologies") or []),
        enabled_recipes=list(progress.get("enabled_recipes") or []),
        craftable_items=list(progress.get("craftable_items") or []),
        mod_names=list(progress.get("mod_names") or []),
        source_save=str(progress.get("source_save") or ""),
        exported_at=progress.get("exported_at"),
    )
    if not snapshot.enabled_recipes:
        return False

    SESSION.apply_progress(snapshot, list(data.get("warnings") or []))
    SESSION.updated_at = data.get("updated_at") or SESSION.updated_at
    SESSION.database_source = str(data.get("database_source") or SESSION.database_source)
    return True
