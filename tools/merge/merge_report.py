"""控制台输出与合并结果写盘（与引擎分离）。"""

from __future__ import annotations

from datetime import datetime

from analysis.report import build_detailed_analysis_lines
from file_analysis import (
    build_console_file_hints,
    build_file_analysis_header_lines,
    build_neutral_notices,
)
from models import MergeRunOptions, MergeRunResult
from scope_rules import format_scope_for_header


def build_report_lines(
    options: MergeRunOptions, result: MergeRunResult
) -> tuple[list[str], list[str]]:
    merge_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stat_lines: list[str] = [
        f"// 合并时间: {merge_time}",
        f"// 来源目录: {options.source_dir}",
        "// 扫描范围: "
        + format_scope_for_header(
            options.source_dir,
            options.merge_max_depth,
            options.merge_scope_exclude,
            options.merge_scope_include,
        ),
    ]
    if options.use_gitignore:
        if options.git_repo_root:
            stat_lines.append(f"// .gitignore: 已启用 (仓库根: {options.git_repo_root})")
        else:
            stat_lines.append("// .gitignore: 已启用 (未检测到 Git 仓库)")
    if options.detail_analysis:
        stat_lines.append("// 语法分析: 详细 (tree-sitter / ana 开)")
    else:
        stat_lines.append("// 语法分析: 粗略 (默认；输入 ana 开启详细)")
    if options.only_relative_paths is not None:
        stat_lines.append(
            f"// 合并模式: c 点名 ({len(options.only_relative_paths)} 个文件)"
        )
    if result.scan_error:
        stat_lines.append(f"// 扫描错误: {result.scan_error}")
    parts = [
        "// 合并统计：共 {} 个文件，总行数 {}".format(
            result.file_count, result.total_lines
        ),
    ]
    ext_bits = [
        "{} 文件 {} 个".format(ext, result.type_file_count.get(ext, 0))
        for ext in options.file_types
    ]
    parts[0] += "，" + "，".join(ext_bits)
    parts[0] += "，读取失败 {} 个文件".format(result.error_count)
    stat_lines.append(parts[0])

    detail_lines: list[str] = []
    if result.project_analysis is not None:
        detail_lines.extend(build_detailed_analysis_lines(result.project_analysis))
        stat_lines.extend(detail_lines)

    if result.file_entries:
        stat_lines.extend(
            build_file_analysis_header_lines(
                result.file_entries,
                options.file_types,
                result.project_analysis,
            )
        )
    stat_lines.append("// ==========================================")
    return stat_lines, detail_lines


def print_scan_banner(source_dir: str, scope_text: str) -> None:
    print(f"🔍 正在扫描目录: {source_dir}")
    print(f"📂 扫描范围: {scope_text}")


def print_merge_summary(result: MergeRunResult, file_types: tuple[str, ...]) -> None:
    print("-" * 30)
    if result.scan_error:
        print(f"⚠️ 扫描目录时出错: {result.scan_error}")
    print(f"✅ 成功! 共处理了 {result.file_count} 个文件，总行数 {result.total_lines}。")
    for ext in file_types:
        print(f"{ext} 文件: {result.type_file_count.get(ext, 0)} 个")
    pa = result.project_analysis
    if pa is not None:
        print(f"详细分析: {pa.total_symbols} 个符号")
        for summary in pa.language_summaries[:5]:
            print(
                f"  [{summary.language}] {summary.file_count} 文件, "
                f"{summary.symbol_count} 符号"
            )
        if pa.skipped_files:
            print(f"  跳过分析: {len(pa.skipped_files)} 个文件（内容已合并）")
        for line in result.console_detail_lines[:6]:
            print(line)
    for line in build_console_file_hints(result.file_entries):
        print(line)
    for line in build_neutral_notices(result):
        print(line)
    print("")


def write_merged_output(output_path: str, result: MergeRunResult) -> None:
    stat_str = "\n".join(result.stat_header_lines) + "\n"
    with open(output_path, "w", encoding="utf-8") as outfile:
        outfile.write(stat_str)
        for chunk in result.merged_chunks:
            outfile.write(chunk)
