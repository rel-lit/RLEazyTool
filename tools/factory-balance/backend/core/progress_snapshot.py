"""存档进度快照。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProgressSnapshot:
    researched_technologies: list[str]
    enabled_recipes: list[str]
    craftable_items: list[str]
    mod_names: list[str]
    source_save: str
    exported_at: str | None = None

    @classmethod
    def from_json(cls, payload: dict, source_save: str) -> ProgressSnapshot:
        return cls(
            researched_technologies=list(payload.get("researched_technologies") or []),
            enabled_recipes=list(payload.get("enabled_recipes") or []),
            craftable_items=list(payload.get("craftable_items") or []),
            mod_names=list(payload.get("mod_names") or []),
            source_save=source_save,
            exported_at=str(payload.get("exported_at_tick")) if payload.get("exported_at_tick") is not None else None,
        )
