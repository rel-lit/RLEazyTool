"""领域模型：配置与合并选项（不含 I/O 细节）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from cs_analyzer import RunningCsStats
from exclude_rules import FileExcludeRule, normalize_exclude_group
from file_analysis import FileEntry


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
    last_exclude_group: Optional[str] = None  # 上次启用/合并成功的组，供 exc 开关恢复
    last_success_exclude_group: Optional[str] = None  # 兼容旧配置，加载时并入 last_exclude_group
    merge_subfolders: bool = True  # 已废弃，仅用于旧配置迁移
    merge_layer_only: bool = False  # 与 merge_max_depth==0 同步，兼容旧配置
    merge_max_depth: int | None = None  # None=不限深度；0=仅本层
    merge_scope_exclude: list[str] = field(default_factory=list)
    merge_scope_include: list[str] = field(default_factory=list)
    scope_enabled: bool = False  # False 时合并不应用 this 范围；细则仍保存在配置中
    c_limit: int = 50
    use_gitignore: bool = False

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "history": self.history,
            "type_groups": self.type_groups,
            "current_type_group": self.current_type_group,
            "last_success_type_group": self.last_success_type_group,
            "exclude_groups": {
                k: normalize_exclude_group(v)
                for k, v in self.exclude_groups.items()
            },
            "current_exclude_group": self.current_exclude_group,
            "last_exclude_group": self.last_exclude_group,
            "last_success_exclude_group": self.last_success_exclude_group,
            "merge_max_depth": self.merge_max_depth,
            "merge_scope_exclude": self.merge_scope_exclude,
            "merge_scope_include": self.merge_scope_include,
            "scope_enabled": self.scope_enabled,
            "c_limit": self.c_limit,
            "use_gitignore": self.use_gitignore,
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
        merge_max_depth = cls._load_merge_max_depth(d)
        merge_scope_exclude = list(d.get("merge_scope_exclude") or [])
        merge_scope_include = list(d.get("merge_scope_include") or [])
        return cls(
            history=history,
            type_groups=type_groups,
            current_type_group=current_type_group,
            last_success_type_group=d.get("last_success_type_group"),
            exclude_groups={
                k: normalize_exclude_group(v)
                for k, v in exclude_groups.items()
            },
            current_exclude_group=d.get("current_exclude_group"),
            last_exclude_group=cls._load_last_exclude_group(d),
            last_success_exclude_group=d.get("last_success_exclude_group"),
            merge_subfolders=d.get("merge_subfolders", True),
            merge_max_depth=merge_max_depth,
            merge_layer_only=cls._load_merge_layer_only(d),
            merge_scope_exclude=merge_scope_exclude,
            merge_scope_include=merge_scope_include,
            scope_enabled=cls._load_scope_enabled(
                d, merge_max_depth, merge_scope_exclude, merge_scope_include
            ),
            c_limit=int(d.get("c_limit", 50)),
            use_gitignore=bool(d.get("use_gitignore", False)),
        )

    @staticmethod
    def _load_last_exclude_group(d: dict[str, Any]) -> str | None:
        if d.get("last_exclude_group"):
            return d.get("last_exclude_group")
        return d.get("last_success_exclude_group")

    @staticmethod
    def _load_scope_enabled(
        d: dict[str, Any],
        merge_max_depth: int | None,
        merge_scope_exclude: list[str],
        merge_scope_include: list[str],
    ) -> bool:
        if "scope_enabled" in d:
            return bool(d["scope_enabled"])
        return (
            merge_max_depth is not None
            or bool(merge_scope_exclude)
            or bool(merge_scope_include)
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
class ScopeSettings:
    max_depth: int | None
    exclude: tuple[str, ...] = ()
    include: tuple[str, ...] = ()


@dataclass(frozen=True)
class MergeRunOptions:
    source_dir: str
    output_path: str
    file_types: tuple[str, ...]
    exc_skip_dirs: tuple[str, ...] = ()
    exc_file_rules: tuple[FileExcludeRule, ...] = ()
    merge_max_depth: int | None = None
    merge_scope_exclude: tuple[str, ...] = ()
    merge_scope_include: tuple[str, ...] = ()
    only_relative_paths: tuple[str, ...] | None = None
    use_gitignore: bool = False
    git_repo_root: str | None = None


@dataclass
class MergeRunResult:
    file_count: int = 0
    error_count: int = 0
    total_lines: int = 0
    type_file_count: dict[str, int] = field(default_factory=dict)
    merged_chunks: list[str] = field(default_factory=list)
    stat_header_lines: list[str] = field(default_factory=list)
    console_detail_lines: list[str] = field(default_factory=list)
    cs_stats: RunningCsStats | None = None
    scan_error: str | None = None
    file_entries: list[FileEntry] = field(default_factory=list)
