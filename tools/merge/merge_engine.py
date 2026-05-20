"""合并引擎：扫描、读文件、生成输出块与统计数据（不 print）。"""

from __future__ import annotations

import os
from typing import Iterator

from constants import EXCLUDE_DIR_NAMES
from cs_analyzer import RunningCsStats, analyze_cs_content
from file_analysis import FileEntry
from merge_report import build_report_lines
from models import MergeRunOptions, MergeRunResult
from scope_rules import ScopeContext, file_in_merge_scope


def _file_passes_filters(
    file: str,
    file_types: tuple[str, ...],
    exclude_words: list[str],
    case_sensitive: bool,
) -> str | None:
    file_check = file if case_sensitive else file.lower()
    if any(
        (w if case_sensitive else w.lower()) in file_check for w in exclude_words
    ):
        return None
    for ext in file_types:
        if file.endswith(ext):
            return ext
    return None


def collect_candidate_paths(
    source_dir: str,
    file_types: tuple[str, ...],
    exclude_words: tuple[str, ...],
    case_sensitive: bool,
    merge_max_depth: int | None,
    scope_exclude: tuple[str, ...] = (),
    scope_include: tuple[str, ...] = (),
) -> tuple[list[str] | None, str | None]:
    """返回 (相对路径列表, 扫描错误)。路径按字典序排序。"""
    exclude_list = list(exclude_words)
    scope = ScopeContext.create(
        source_dir, merge_max_depth, scope_exclude, scope_include
    )
    rel_paths: list[str] = []
    for item in _iter_scoped_file_pairs(source_dir, merge_max_depth):
        if item[0] is None:
            return None, item[1]
        root, file = item[0], item[1]
        if _file_passes_filters(file, file_types, exclude_list, case_sensitive) is None:
            continue
        file_path = os.path.join(root, file)
        rel = os.path.relpath(file_path, source_dir)
        if not file_in_merge_scope(rel, scope):
            continue
        rel_paths.append(rel)
    rel_paths.sort()
    return rel_paths, None


def _iter_scoped_file_pairs(
    source_dir: str, max_depth: int | None
) -> Iterator[tuple[str, str] | tuple[None, str]]:
    if max_depth == 0:
        try:
            for name in sorted(os.listdir(source_dir)):
                path = os.path.join(source_dir, name)
                if os.path.isfile(path):
                    yield source_dir, name
        except OSError as e:
            yield None, str(e)
        return
    try:
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIR_NAMES]
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
    exclude_words = list(options.exclude_words)
    case_sensitive = options.case_sensitive
    result = MergeRunResult(
        type_file_count={ext: 0 for ext in options.file_types},
        cs_stats=RunningCsStats() if ".cs" in options.file_types else None,
    )
    merged: list[str] = []

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
            file_name = os.path.basename(file_path)
            matched_ext = _file_passes_filters(
                file_name, options.file_types, exclude_words, case_sensitive
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
        for item in _iter_scoped_file_pairs(options.source_dir, scope.max_depth):
            if item[0] is None:
                result.scan_error = item[1]
                break
            root, file = item[0], item[1]
            matched_ext = _file_passes_filters(
                file, options.file_types, exclude_words, case_sensitive
            )
            if matched_ext is None:
                continue
            file_path = os.path.join(root, file)
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
