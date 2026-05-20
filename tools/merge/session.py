"""从 REPL 会话构建合并选项与过滤器设置。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from exc_handlers import exc_filter_from_config
from gitignore_support import GitIgnoreMatcher, find_git_root
from models import MergeConfig, MergeRunOptions, ScopeSettings

if TYPE_CHECKING:
    from repl import MergeRepl


def filter_settings_from_config(
    config: MergeConfig,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple]:
    file_types = tuple(
        config.type_groups.get(config.current_type_group, [".cs"])
    )
    exc_skip_dirs, exc_file_rules = exc_filter_from_config(config)
    return file_types, exc_skip_dirs, exc_file_rules


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
    file_types, exc_skip_dirs, exc_file_rules = filter_settings_from_config(
        repl.config
    )
    scope = scope_settings_from_config(repl.config)
    git_root: str | None = None
    if repl.config.use_gitignore:
        git_root = find_git_root(repl.current_path)
    return MergeRunOptions(
        source_dir=repl.current_path,
        output_path=output_path,
        file_types=file_types,
        exc_skip_dirs=exc_skip_dirs,
        exc_file_rules=exc_file_rules,
        merge_max_depth=scope.max_depth,
        merge_scope_exclude=scope.exclude,
        merge_scope_include=scope.include,
        only_relative_paths=only_relative_paths,
        use_gitignore=repl.config.use_gitignore,
        git_repo_root=git_root,
    )


def load_gitignore_matcher(config: MergeConfig, source_dir: str) -> GitIgnoreMatcher | None:
    if not config.use_gitignore:
        return None
    return GitIgnoreMatcher.load(source_dir)
