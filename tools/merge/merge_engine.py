"""合并引擎：扫描、读文件、生成输出块与统计数据（不 print）。"""

from __future__ import annotations

import os
from typing import Iterator

from exclude_rules import FileExcludeRule, filename_excluded, walk_skip_dir_names
from cs_analyzer import RunningCsStats, analyze_cs_content
from file_analysis import FileEntry
from gitignore_support import GitIgnoreMatcher
from merge_report import build_report_lines
from models import MergeRunOptions, MergeRunResult
from scope_rules import ScopeContext, file_in_merge_scope


def _file_passes_filters(
    file: str,
    file_types: tuple[str, ...],
    exc_file_rules: tuple[FileExcludeRule, ...],
) -> str | None:
    if filename_excluded(file, exc_file_rules):
        return None
    for ext in file_types:
        if file.endswith(ext):
            return ext
    return None


def _prune_dirs(
    root: str,
    source_dir: str,
    dirs: list[str],
    skip_dirs: frozenset[str],
    gitignore: GitIgnoreMatcher | None,
) -> None:
    kept: list[str] = []
    for d in dirs:
        if d in skip_dirs:
            continue
        if gitignore is not None:
            abs_d = os.path.join(root, d)
            if gitignore.ignores_dir(abs_d):
                continue
        kept.append(d)
    dirs[:] = kept


def collect_candidate_paths(
    source_dir: str,
    file_types: tuple[str, ...],
    exc_skip_dirs: tuple[str, ...],
    exc_file_rules: tuple[FileExcludeRule, ...],
    merge_max_depth: int | None,
    scope_exclude: tuple[str, ...] = (),
    scope_include: tuple[str, ...] = (),
    *,
    gitignore: GitIgnoreMatcher | None = None,
) -> tuple[list[str] | None, str | None]:
    """返回 (相对路径列表, 扫描错误)。路径按字典序排序。"""
    scope = ScopeContext.create(
        source_dir, merge_max_depth, scope_exclude, scope_include
    )
    skip_dirs = walk_skip_dir_names(exc_skip_dirs)
    rel_paths: list[str] = []
    for item in _iter_scoped_file_pairs(
        source_dir, merge_max_depth, skip_dirs, gitignore
    ):
        if item[0] is None:
            return None, item[1]
        root, file = item[0], item[1]
        if _file_passes_filters(file, file_types, exc_file_rules) is None:
            continue
        file_path = os.path.join(root, file)
        if gitignore is not None and gitignore.ignores_file(file_path):
            continue
        rel = os.path.relpath(file_path, source_dir)
        if not file_in_merge_scope(rel, scope):
            continue
        rel_paths.append(rel)
    rel_paths.sort()
    return rel_paths, None


def _iter_scoped_file_pairs(
    source_dir: str,
    max_depth: int | None,
    skip_dirs: frozenset[str],
    gitignore: GitIgnoreMatcher | None,
) -> Iterator[tuple[str, str] | tuple[None, str]]:
    if max_depth == 0:
        try:
            for name in sorted(os.listdir(source_dir)):
                path = os.path.join(source_dir, name)
                if os.path.isfile(path):
                    if gitignore is not None and gitignore.ignores_file(path):
                        continue
                    yield source_dir, name
        except OSError as e:
            yield None, str(e)
        return
    try:
        for root, dirs, files in os.walk(source_dir):
            _prune_dirs(root, source_dir, dirs, skip_dirs, gitignore)
            if max_depth is not None:
                rel_root = os.path.relpath(root, source_dir)
                if rel_root == ".":
                    rel_root = ""
                rel_root = rel_root.replace("\\", "/")
                pruned: list[str] = []
                for d in dirs:
                    child = f"{rel_root}/{d}" if rel_root else d
                    if child.count("/") + 1 <= max_depth:
                        pruned.append(d)
                dirs[:] = pruned
            for file in files:
                yield root, file
    except OSError as e:
        yield None, str(e)


def _merge_one_file(
    file_path: str,
    relative_path: str,
    matched_ext: str,
    merged: list[str],
    result: MergeRunResult,
) -> None:
    cs = result.cs_stats
    merged.append(
        f"\n\n// ==================== 文件: {relative_path} ====================\n\n"
    )
    try:
        size_bytes = os.path.getsize(file_path)
        with open(file_path, encoding="utf-8", errors="ignore") as infile:
            content = infile.read()
        line_count = len(content.splitlines())
        result.total_lines += line_count
        result.type_file_count[matched_ext] += 1
        if matched_ext == ".cs" and cs is not None:
            analyze_cs_content(cs, content)
        merged.append(content)
        result.file_count += 1
        result.file_entries.append(
            FileEntry(
                relative_path=relative_path,
                lines=line_count,
                size_bytes=size_bytes,
                ext=matched_ext,
            )
        )
    except OSError as e:
        merged.append(f"// [错误] 无法读取文件: {e}\n")
        result.error_count += 1


def run_merge(options: MergeRunOptions) -> MergeRunResult:
    result = MergeRunResult(
        type_file_count={ext: 0 for ext in options.file_types},
        cs_stats=RunningCsStats() if ".cs" in options.file_types else None,
    )
    merged: list[str] = []
    skip_dirs = walk_skip_dir_names(options.exc_skip_dirs)
    exc_rules = options.exc_file_rules
    gitignore: GitIgnoreMatcher | None = None
    if options.use_gitignore:
        from gitignore_support import GitIgnoreMatcher as _G

        gitignore = _G.load(options.source_dir)

    if options.only_relative_paths is not None:
        for relative_path in sorted(options.only_relative_paths):
            file_path = os.path.join(options.source_dir, relative_path)
            if not os.path.isfile(file_path):
                merged.append(
                    f"\n\n// ==================== 文件: {relative_path} ====================\n\n"
                )
                merged.append("// [错误] 文件不存在或不可读\n")
                result.error_count += 1
                continue
            if gitignore is not None and gitignore.ignores_file(file_path):
                continue
            file_name = os.path.basename(file_path)
            matched_ext = _file_passes_filters(
                file_name, options.file_types, exc_rules
            )
            if matched_ext is None:
                continue
            _merge_one_file(
                file_path, relative_path, matched_ext, merged, result
            )
    else:
        scope = ScopeContext.create(
            options.source_dir,
            options.merge_max_depth,
            options.merge_scope_exclude,
            options.merge_scope_include,
        )
        for item in _iter_scoped_file_pairs(
            options.source_dir, scope.max_depth, skip_dirs, gitignore
        ):
            if item[0] is None:
                result.scan_error = item[1]
                break
            root, file = item[0], item[1]
            matched_ext = _file_passes_filters(
                file, options.file_types, exc_rules
            )
            if matched_ext is None:
                continue
            file_path = os.path.join(root, file)
            if gitignore is not None and gitignore.ignores_file(file_path):
                continue
            relative_path = os.path.relpath(file_path, options.source_dir)
            if not file_in_merge_scope(relative_path, scope):
                continue
            _merge_one_file(
                file_path, relative_path, matched_ext, merged, result
            )

    result.merged_chunks = merged
    result.stat_header_lines, result.console_detail_lines = build_report_lines(
        options, result
    )
    return result
