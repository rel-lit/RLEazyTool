"""合并结果中的文件级统计（写入输出文件头部；终端仅摘要）。"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

FULL_FILE_LIST_MAX = 100
PARTIAL_FILE_LIST_TOP = 20
CONSOLE_TOP_FILES = 5


@dataclass
class FileEntry:
    relative_path: str
    lines: int
    size_bytes: int
    ext: str


def format_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.2f} MB"


def _top_level_dir(relative_path: str) -> str:
    parts = relative_path.replace("\\", "/").split("/")
    if len(parts) <= 1:
        return "(当前目录)"
    return parts[0]


def _line_stats(entries: list[FileEntry]) -> tuple[float, int, int, float]:
    if not entries:
        return 0.0, 0, 0, 0.0
    lines = [e.lines for e in entries]
    return (
        round(sum(lines) / len(lines), 1),
        min(lines),
        max(lines),
        float(median(lines)),
    )


def build_file_analysis_header_lines(
    entries: list[FileEntry],
    file_types: tuple[str, ...],
    project_analysis=None,
) -> list[str]:
    """详细分析块，仅写入合并 txt 头部。"""
    if not entries:
        return []

    lines: list[str] = ["// --- 文件分析 ---"]
    total_bytes = sum(e.size_bytes for e in entries)
    avg_l, min_l, max_l, med_l = _line_stats(entries)
    lines.append(
        "// 体量: 总大小 {}，单文件行数 平均 {} / 中位 {} / 最小 {} / 最大 {}".format(
            format_size(total_bytes), avg_l, med_l, min_l, max_l
        )
    )

    lines.append("// 按后缀:")
    for ext in file_types:
        group = [e for e in entries if e.ext == ext]
        if not group:
            continue
        g_lines = sum(e.lines for e in group)
        avg = round(g_lines / len(group), 1) if group else 0
        lines.append(
            f"//   {ext}: {len(group)} 个, 共 {g_lines} 行, 平均 {avg} 行/文件"
        )

    dir_map: dict[str, list[FileEntry]] = {}
    for e in entries:
        key = _top_level_dir(e.relative_path)
        dir_map.setdefault(key, []).append(e)
    if len(dir_map) > 1 or next(iter(dir_map), None) != "(当前目录)":
        lines.append("// 按顶层目录:")
        for name in sorted(dir_map.keys()):
            group = dir_map[name]
            lines.append(
                f"//   {name}: {len(group)} 个文件, {sum(e.lines for e in group)} 行"
            )

    sorted_by_lines = sorted(entries, key=lambda e: e.lines, reverse=True)
    lines.append("// 行数最多的文件 (Top {}):".format(PARTIAL_FILE_LIST_TOP))
    for e in sorted_by_lines[:PARTIAL_FILE_LIST_TOP]:
        lines.append(
            f"//   {e.lines:5d} 行  {format_size(e.size_bytes):>10}  {e.relative_path}"
        )

    if project_analysis and project_analysis.top_symbols_by_span:
        lines.append("// 符号体量 Top 5 (详细分析):")
        for path, name, span, kind in project_analysis.top_symbols_by_span[:5]:
            lines.append(f"//   {span:5d} 行  [{kind}] {name}  @ {path}")

    lines.append("// 文件清单:")
    if len(entries) <= FULL_FILE_LIST_MAX:
        for e in sorted(entries, key=lambda x: x.relative_path):
            lines.append(
                f"//   {e.lines:5d} 行  {format_size(e.size_bytes):>10}  {e.relative_path}"
            )
    else:
        lines.append(
            f"//   (共 {len(entries)} 个，超过 {FULL_FILE_LIST_MAX}，仅列出行数 Top {PARTIAL_FILE_LIST_TOP}；完整列表见上)"
        )
        for e in sorted_by_lines[:PARTIAL_FILE_LIST_TOP]:
            lines.append(
                f"//   {e.lines:5d} 行  {format_size(e.size_bytes):>10}  {e.relative_path}"
            )

    lines.append("// --- 文件分析结束 ---")
    return lines


def build_console_file_hints(entries: list[FileEntry]) -> list[str]:
    """终端用：简短提示，不刷屏。"""
    if not entries:
        return []
    out: list[str] = []
    avg_l, min_l, max_l, med_l = _line_stats(entries)
    total_bytes = sum(e.size_bytes for e in entries)
    out.append(
        f"📊 体量: {format_size(total_bytes)} | 行数 均{avg_l} 中位{med_l} 范围[{min_l}-{max_l}]"
    )
    top = sorted(entries, key=lambda e: e.lines, reverse=True)[:CONSOLE_TOP_FILES]
    out.append("📊 行数 Top{}:".format(len(top)))
    for e in top:
        out.append(f"   {e.lines:5d} 行  {e.relative_path}")
    return out


def build_neutral_notices(result) -> list[str]:
    """中性提醒（仅终端，每条一行）。"""
    notes: list[str] = []
    if result.error_count > 0:
        notes.append(f"⚠️ 有 {result.error_count} 个文件读取失败，请检查权限或路径。")
    if result.file_count >= 50:
        notes.append(
            f"ℹ️ 已合并 {result.file_count} 个文件，输出体积可能较大，请注意磁盘与编辑器性能。"
        )
    elif result.file_count >= 20:
        notes.append(f"ℹ️ 已合并 {result.file_count} 个文件。")
    if result.total_lines >= 5000:
        notes.append(
            f"ℹ️ 总行数 {result.total_lines}，建议分段查看或使用支持大文件的编辑器。"
        )
    pa = result.project_analysis
    if pa and pa.top_symbols_by_span:
        top_span = pa.top_symbols_by_span[0][2]
        if top_span > 200:
            notes.append(
                f"ℹ️ 最大符号跨度约 {top_span} 行，可考虑拆分过大类型/函数。"
            )
    return notes
