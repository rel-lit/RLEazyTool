"""单文件 / 项目级分析管线。"""

from __future__ import annotations

from .registry import language_for_ext
from .ts_analyzer import analyze_with_tree_sitter
from .types import FileAnalysisResult, LanguageSummary, ProjectAnalysis


def analyze_file_detailed(
    relative_path: str,
    ext: str,
    content: str,
) -> FileAnalysisResult:
    lang_key = language_for_ext(ext)
    if lang_key is None:
        return FileAnalysisResult(
            relative_path=relative_path,
            ext=ext,
            language=None,
            ok=False,
            error="该后缀无 tree-sitter 语法支持，已跳过详细分析",
        )
    try:
        return analyze_with_tree_sitter(
            lang_key,
            content,
            relative_path=relative_path,
            ext=ext,
        )
    except Exception as e:
        return FileAnalysisResult(
            relative_path=relative_path,
            ext=ext,
            language=lang_key,
            ok=False,
            error=str(e),
        )


def aggregate_project(file_results: list[FileAnalysisResult]) -> ProjectAnalysis:
    by_lang: dict[str, LanguageSummary] = {}
    spans: list[tuple[str, str, int, str]] = []
    skipped: list[tuple[str, str]] = []
    total = 0

    for fr in file_results:
        if not fr.ok:
            skipped.append((fr.relative_path, fr.error or "未知错误"))
            continue
        lang = fr.language or "unknown"
        summary = by_lang.setdefault(lang, LanguageSummary(language=lang))
        summary.file_count += 1
        for sym in fr.symbols:
            total += 1
            summary.symbol_count += 1
            summary.kind_counts[sym.kind] = summary.kind_counts.get(sym.kind, 0) + 1
            span = sym.line_end - sym.line_start + 1
            spans.append((fr.relative_path, sym.name, span, sym.kind))

    spans.sort(key=lambda x: x[2], reverse=True)
    return ProjectAnalysis(
        language_summaries=sorted(by_lang.values(), key=lambda s: s.language),
        top_symbols_by_span=spans[:30],
        skipped_files=skipped,
        total_symbols=total,
    )
