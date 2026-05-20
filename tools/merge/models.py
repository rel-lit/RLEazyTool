"""领域模型：配置与合并选项（不含 I/O 细节）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MergeConfig:
    history: list[str] = field(default_factory=list)
    type_groups: dict[str, list[str]] = field(
        default_factory=lambda: {"default": [".cs"]}
    )
    current_type_group: str = "default"
    last_success_type_group: str | None = None
    exclude_groups: dict[str, dict[str, Any]] = field(default_factory=dict)
    current_exclude_group: Optional[str] = None
    last_success_exclude_group: Optional[str] = None
    merge_subfolders: bool = True  # 已废弃，仅用于旧配置迁移
    merge_layer_only: bool = False  # 与 merge_max_depth==0 同步，兼容旧配置
    merge_max_depth: int | None = None  # None=不限深度；0=仅本层
    merge_scope_exclude: list[str] = field(default_factory=list)
    merge_scope_include: list[str] = field(default_factory=list)
    c_limit: int = 50

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "history": self.history,
            "type_groups": self.type_groups,
            "current_type_group": self.current_type_group,
            "last_success_type_group": self.last_success_type_group,
            "exclude_groups": self.exclude_groups,
            "current_exclude_group": self.current_exclude_group,
            "last_success_exclude_group": self.last_success_exclude_group,
            "merge_subfolders": self.merge_subfolders,
            "merge_layer_only": self.merge_layer_only,
            "merge_max_depth": self.merge_max_depth,
            "merge_scope_exclude": self.merge_scope_exclude,
            "merge_scope_include": self.merge_scope_include,
            "c_limit": self.c_limit,
        }

    @classmethod
    def from_json_data(cls, data: Any) -> MergeConfig:
        if isinstance(data, list):
            return cls(history=list(data))
        if not isinstance(data, dict):
            return cls()
        d = data
        history = list(d.get("history", []))
        type_groups = d.get("type_groups") or {"default": [".cs"]}
        current_type_group = d.get("current_type_group", "default")
        exclude_groups = d.get("exclude_groups") or {}
        return cls(
            history=history,
            type_groups=type_groups,
            current_type_group=current_type_group,
            last_success_type_group=d.get("last_success_type_group"),
            exclude_groups=exclude_groups,
            current_exclude_group=d.get("current_exclude_group"),
            last_success_exclude_group=d.get("last_success_exclude_group"),
            merge_subfolders=d.get("merge_subfolders", True),
            merge_max_depth=cls._load_merge_max_depth(d),
            merge_layer_only=cls._load_merge_layer_only(d),
            merge_scope_exclude=list(d.get("merge_scope_exclude") or []),
            merge_scope_include=list(d.get("merge_scope_include") or []),
            c_limit=int(d.get("c_limit", 50)),
        )

    @staticmethod
    def _load_merge_max_depth(d: dict[str, Any]) -> int | None:
        if "merge_max_depth" in d:
            raw = d["merge_max_depth"]
            return None if raw is None else int(raw)
        if d.get("merge_layer_only") or (
            "merge_layer_only" not in d and not d.get("merge_subfolders", True)
        ):
            return 0
        return None

    @staticmethod
    def _load_merge_layer_only(d: dict[str, Any]) -> bool:
        if "merge_max_depth" in d:
            return d["merge_max_depth"] == 0
        if "merge_layer_only" in d:
            return bool(d["merge_layer_only"])
        return not d.get("merge_subfolders", True)


@dataclass(frozen=True)
class MergeRunOptions:
    source_dir: str
    output_path: str
    file_types: tuple[str, ...]
    exclude_words: tuple[str, ...] = ()
    case_sensitive: bool = True
    recursive: bool = True  # 已废弃
    merge_max_depth: int | None = None
    merge_scope_exclude: tuple[str, ...] = ()
    merge_scope_include: tuple[str, ...] = ()
    only_relative_paths: tuple[str, ...] | None = None
