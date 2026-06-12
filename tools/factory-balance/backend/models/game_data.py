"""游戏数据四层模型（与运行时 dataclass 分离的语义层）。

1. GameVersionKey + RecipePack  — 版本维度的「全配方 + 本地化」
2. SaveProgressRecord           — 存档进度（全配方上的过滤视图）
3. RecipeRecord                 — 单条配方（产出 / 原料 / 类别）
4. ItemRecord                   — 单种物品（名称 / 本地化 / 贴图等）
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GameVersionKey:
    """唯一标识一次「游戏版本 + 模组组合 + 语言」。"""

    factorio_version: str
    mods: tuple[str, ...]
    locale: str = "zh-CN"

    @classmethod
    def create(
        cls,
        factorio_version: str | None,
        mod_names: list[str] | None,
        *,
        locale: str = "zh-CN",
    ) -> GameVersionKey:
        version = (factorio_version or "unknown").strip()
        mods = tuple(sorted({m for m in (mod_names or []) if m and m != "factory-balance-sync"}))
        return cls(factorio_version=version, mods=mods, locale=locale)

    def pack_slug(self) -> str:
        """用于 cache/packs/ 下的目录名。"""
        mod_part = "_".join(self.mods) if self.mods else "vanilla"
        mod_part = re.sub(r"[^\w.-]+", "-", mod_part)[:120]
        ver = re.sub(r"[^\w.-]+", "-", self.factorio_version)
        return f"{ver}__{mod_part}__{self.locale}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "factorio_version": self.factorio_version,
            "mods": list(self.mods),
            "locale": self.locale,
            "pack_slug": self.pack_slug(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GameVersionKey:
        return cls(
            factorio_version=str(data.get("factorio_version") or "unknown"),
            mods=tuple(sorted(str(m) for m in (data.get("mods") or []))),
            locale=str(data.get("locale") or "zh-CN"),
        )


@dataclass
class ItemRecord:
    name: str
    label: str
    is_raw: bool = False
    expansion: str = "base"
    group: str | None = None
    icon: str | None = None
    prototype_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "is_raw": self.is_raw,
            "expansion": self.expansion,
            "group": self.group,
            "icon": self.icon,
            "prototype_type": self.prototype_type,
        }


@dataclass
class RecipeRecord:
    name: str
    label: str
    category: str
    energy: float
    ingredients: list[dict[str, Any]]
    products: list[dict[str, Any]]
    expansion: str = "base"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "category": self.category,
            "energy": self.energy,
            "ingredients": self.ingredients,
            "products": self.products,
            "expansion": self.expansion,
        }


@dataclass
class RecipePack:
    """层 1：某一版本下的完整配方库 + 本地化索引。"""

    version_key: GameVersionKey
    items: dict[str, ItemRecord] = field(default_factory=dict)
    recipes: dict[str, RecipeRecord] = field(default_factory=dict)
    dump_path: Path | None = None
    locale_path: Path | None = None
    created_at: str | None = None

    def manifest_dict(self) -> dict[str, Any]:
        return {
            "version_key": self.version_key.to_dict(),
            "item_count": len(self.items),
            "recipe_count": len(self.recipes),
            "dump_file": self.dump_path.name if self.dump_path else None,
            "locale_file": self.locale_path.name if self.locale_path else None,
            "created_at": self.created_at,
        }


@dataclass
class SaveProgressRecord:
    """层 2：存档进度 = 对 RecipePack 的「已解锁子集」。"""

    version_key: GameVersionKey | None
    source_save: str
    save_mtime: float | None = None
    researched_technologies: list[str] = field(default_factory=list)
    enabled_recipes: list[str] = field(default_factory=list)
    mod_names: list[str] = field(default_factory=list)
    exported_at_tick: str | None = None
    cached_at: str | None = None

    @property
    def enabled_recipe_set(self) -> set[str]:
        return set(self.enabled_recipes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version_key": self.version_key.to_dict() if self.version_key else None,
            "source_save": self.source_save,
            "save_mtime": self.save_mtime,
            "researched_technologies": self.researched_technologies,
            "enabled_recipes": self.enabled_recipes,
            "mod_names": self.mod_names,
            "exported_at_tick": self.exported_at_tick,
            "cached_at": self.cached_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SaveProgressRecord:
        vk = data.get("version_key")
        return cls(
            version_key=GameVersionKey.from_dict(vk) if isinstance(vk, dict) else None,
            source_save=str(data.get("source_save") or ""),
            save_mtime=float(data["save_mtime"]) if data.get("save_mtime") is not None else None,
            researched_technologies=list(data.get("researched_technologies") or []),
            enabled_recipes=list(data.get("enabled_recipes") or []),
            mod_names=list(data.get("mod_names") or []),
            exported_at_tick=data.get("exported_at_tick"),
            cached_at=data.get("cached_at"),
        )


def mods_fingerprint(mod_names: list[str]) -> str:
    payload = json.dumps(sorted(set(mod_names)), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
