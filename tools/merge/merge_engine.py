"""合并引擎：只负责扫描、读文件、生成输出块与统计数据结构；不 print。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator

from constants import EXCLUDE_DIR_NAMES
from cs_analyzer import RunningCsStats, analyze_cs_content
from models import MergeRunOptions


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
    recursive: bool,
) -> tuple[list[str] | None, str | None]:
    """返回 (相对路径列表, 扫描错误)。路径按字典序排序。"""
    exclude_list = list(exclude_words)
    rel_paths: list[str] = []
    for item in _iter_file_pairs(source_dir, recursive):
        if item[0] is None:
            return None, item[1]
        root, file = item[0], item[1]
        if _file_passes_filters(file, file_types, exclude_list, case_sensitive) is None:
            continue
        file_path = os.path.join(root, file)
        rel_paths.append(os.path.relpath(file_path, source_dir))
    rel_paths.sort()
    return rel_paths, None


def _iter_file_pairs(
    source_dir: str, recursive: bool
) -> Iterator[tuple[str, str] | tuple[None, str]]:
    """产出 (root, filename)；若无法列出目录则产出 (None, error_message) 一次后结束。"""
    if recursive:
        try:
            for root, dirs, files in os.walk(source_dir):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIR_NAMES]
                for file in files:
                    yield root, file
        except OSError as e:
            yield None, str(e)
        return
    try:
        for name in sorted(os.listdir(source_dir)):
            path = os.path.join(source_dir, name)
            if os.path.isfile(path):
                yield source_dir, name
    except OSError as e:
        yield None, str(e)


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


def _merge_one_file(
    options: MergeRunOptions,
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
        with open(file_path, encoding="utf-8", errors="ignore") as infile:
            content = infile.read()
        result.total_lines += len(content.splitlines())
        result.type_file_count[matched_ext] += 1
        if matched_ext == ".cs" and cs is not None:
            analyze_cs_content(cs, content)
        merged.append(content)
        result.file_count += 1
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
                merged.append(f"// [错误] 文件不存在或不可读\n")
                result.error_count += 1
                continue
            file_name = os.path.basename(file_path)
            matched_ext = _file_passes_filters(
                file_name, options.file_types, exclude_words, case_sensitive
            )
            if matched_ext is None:
                continue
            _merge_one_file(
                options, file_path, relative_path, matched_ext, merged, result
            )
    else:
        for item in _iter_file_pairs(options.source_dir, options.recursive):
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
            _merge_one_file(
                options, file_path, relative_path, matched_ext, merged, result
            )

    result.merged_chunks = merged
    result.stat_header_lines, result.console_detail_lines = _build_report_lines(
        options, result
    )
    return result


def _build_report_lines(
    options: MergeRunOptions, result: MergeRunResult
) -> tuple[list[str], list[str]]:
    merge_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stat_lines: list[str] = [
        f"// 合并时间: {merge_time}",
        f"// 来源目录: {options.source_dir}",
        "// 扫描范围: "
        + ("含子文件夹" if options.recursive else "仅当前文件夹（不含子目录）"),
    ]
    if options.only_relative_paths is not None:
        stat_lines.append(
            f"// 合并模式: c 点名 ({len(options.only_relative_paths)} 个文件)"
        )
    if result.scan_error:
        stat_lines.append(f"// 扫描错误: {result.scan_error}")
    parts = [
        "// 合并统计：共 {} 个文件，总行数 {}".format(result.file_count, result.total_lines),
    ]
    ext_bits = [
        "{} 文件 {} 个".format(ext, result.type_file_count.get(ext, 0))
        for ext in options.file_types
    ]
    parts[0] += "，" + "，".join(ext_bits)
    cs = result.cs_stats
    if ".cs" in options.file_types and cs is not None:
        parts[0] += (
            "，类 {} 个，结构体 {} 个，枚举 {} 个，接口 {} 个，"
            "变量/字段/属性 {} 个，方法 {} 个".format(
                cs.class_count,
                cs.struct_count,
                cs.enum_count,
                cs.interface_count,
                cs.variable_count,
                cs.method_count,
            )
        )
    parts[0] += "，读取失败 {} 个文件".format(result.error_count)
    stat_lines.append(parts[0])

    detail_lines: list[str] = []
    if ".cs" in options.file_types and cs is not None and cs.cs_class_infos:
        infos = cs.cs_class_infos
        real_classes = [c for c in infos if not c[0] and not c[1]]
        abstract_classes = [c for c in infos if c[0] and not c[1]]
        interfaces = [c for c in infos if c[1]]
        avg_real = (
            round(sum(c[3] for c in real_classes) / len(real_classes), 2)
            if real_classes
            else 0
        )
        avg_abs_m = (
            round(sum(c[6] for c in abstract_classes) / len(abstract_classes), 2)
            if abstract_classes
            else 0
        )
        max_len = max((c[3] for c in infos), default=0)
        min_len = min((c[3] for c in infos), default=0)
        avg_m = (
            round(sum(c[4] for c in infos) / len(infos), 2) if infos else 0
        )
        avg_f = (
            round(sum(c[5] for c in infos) / len(infos), 2) if infos else 0
        )
        avg_enum = (
            round(
                sum(cs.enum_member_counts) / len(cs.enum_member_counts),
                2,
            )
            if cs.enum_member_counts
            else 0
        )
        avg_struct_f = (
            round(
                sum(cs.struct_field_counts) / len(cs.struct_field_counts),
                2,
            )
            if cs.struct_field_counts
            else 0
        )
        avg_iface_m = (
            round(sum(c[4] for c in interfaces) / len(interfaces), 2)
            if interfaces
            else 0
        )
        line_a = (
            "// 实际类平均长度: {} 行，抽象类平均抽象方法数: {}，"
            "最大类长度: {}，最小类长度: {}".format(
                avg_real, avg_abs_m, max_len, min_len
            )
        )
        line_b = "// 平均每类方法数: {}，平均每类字段数: {}".format(avg_m, avg_f)
        line_c = (
            "// 枚举平均成员数: {}，结构体平均字段数: {}，接口平均方法数: {}".format(
                avg_enum, avg_struct_f, avg_iface_m
            )
        )
        stat_lines.extend([line_a, line_b, line_c])
        detail_lines = [
            line_a.replace("// ", ""),
            line_b.replace("// ", ""),
            line_c.replace("// ", ""),
        ]
    stat_lines.append("// ==========================================")
    return stat_lines, detail_lines
