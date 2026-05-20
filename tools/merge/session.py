"""从 REPL 会话构建合并选项与过滤器设置。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from models import MergeConfig, MergeRunOptions, ScopeSettings

if TYPE_CHECKING:
    from repl import MergeRepl


def filter_settings_from_config(
    config: MergeConfig,
) -> tuple[tuple[str, ...], tuple[str, ...], bool]:
    file_types = tuple(
        config.type_groups.get(config.current_type_group, [".cs"])
    )
    exclude_words: tuple[str, ...] = ()
    case_sensitive = True
    exc_group = config.current_exclude_group
    if exc_group and exc_group in config.exclude_groups:
        g = config.exclude_groups[exc_group]
        exclude_words = tuple(g["words"])
        case_sensitive = g.get("case_sensitive", True)
    return file_types, exclude_words, case_sensitive


def scope_settings_from_config(config: MergeConfig) -> ScopeSettings:
    return ScopeSettings(
        max_depth=config.merge_max_depth,
        exclude=tuple(config.merge_scope_exclude),
        include=tuple(config.merge_scope_include),
    )


def build_run_options(
    repl: "MergeRepl",
    output_path: str,
    *,
    only_relative_paths: tuple[str, ...] | None = None,
) -> MergeRunOptions:
    file_types, exclude_words, case_sensitive = filter_settings_from_config(
        repl.config
    )
    scope = scope_settings_from_config(repl.config)
    return MergeRunOptions(
        source_dir=repl.current_path,
        output_path=output_path,
        file_types=file_types,
        exclude_words=exclude_words,
        case_sensitive=case_sensitive,
        merge_max_depth=scope.max_depth,
        merge_scope_exclude=scope.exclude,
        merge_scope_include=scope.include,
        only_relative_paths=only_relative_paths,
    )
