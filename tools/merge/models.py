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
    merge_subfolders: bool = True
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
            c_limit=int(d.get("c_limit", 50)),
        )


@dataclass(frozen=True)
class MergeRunOptions:
    source_dir: str
    output_path: str
    file_types: tuple[str, ...]
    exclude_words: tuple[str, ...] = ()
    case_sensitive: bool = True
    recursive: bool = True
    only_relative_paths: tuple[str, ...] | None = None
