"""分析结果 → 合并报告注释行。"""

from __future__ import annotations

from .types import FileAnalysisResult, ProjectAnalysis


def build_detailed_analysis_lines(project: ProjectAnalysis) -> list[str]:
    if not project.language_summaries and not project.skipped_files:
        return []

    lines: list[str] = [
        "// --- 详细语法分析（tree-sitter，IDE 级符号）---",
        f"// 符号总数: {project.total_symbols}",
    ]
    for summary in project.language_summaries:
        kinds = ", ".join(
            f"{k} {v}" for k, v in sorted(summary.kind_counts.items())
        )
        lines.append(
            f"//   [{summary.language}] {summary.file_count} 个文件, "
            f"{summary.symbol_count} 个符号"
            + (f" ({kinds})" if kinds else "")
        )

    if project.top_symbols_by_span:
        lines.append("// 体量最大的符号 (Top 15, 按行跨度):")
        for path, name, span, kind in project.top_symbols_by_span[:15]:
            lines.append(f"//   {span:4d} 行  [{kind}] {name}  @ {path}")

    if project.skipped_files:
        lines.append(f"// 详细分析跳过 {len(project.skipped_files)} 个文件（内容仍已合并）:")
        for path, err in project.skipped_files[:20]:
            lines.append(f"//   {path}: {err}")
        if len(project.skipped_files) > 20:
            lines.append(f"//   … 还有 {len(project.skipped_files) - 20} 个")

    lines.append("// --- 详细分析结束 ---")
    return lines


def build_per_file_detail_block(fr: FileAnalysisResult) -> list[str]:
    """可选：单文件符号列表（仅成功且符号较少时）。"""
    if not fr.ok or not fr.symbols or len(fr.symbols) > 80:
        return []
    lines = [f"// [分析] {fr.relative_path} ({fr.language})"]
    for sym in fr.symbols[:40]:
        parent = f" in {sym.parent}" if sym.parent else ""
        lines.append(
            f"//   L{sym.line_start}-{sym.line_end} [{sym.kind}] {sym.name}{parent}"
        )
    if len(fr.symbols) > 40:
        lines.append(f"//   … 还有 {len(fr.symbols) - 40} 个符号")
    return lines
