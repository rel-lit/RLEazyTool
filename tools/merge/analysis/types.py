"""合并结果的结构化分析模型。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SymbolInfo:
    kind: str
    name: str
    line_start: int
    line_end: int
    parent: str | None = None
    extra: str | None = None


@dataclass
class FileAnalysisResult:
    relative_path: str
    ext: str
    language: str | None
    ok: bool
    error: str | None = None
    symbols: list[SymbolInfo] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)


@dataclass
class LanguageSummary:
    language: str
    file_count: int = 0
    symbol_count: int = 0
    kind_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class ProjectAnalysis:
    """跨文件汇总（详细分析模式）。"""

    language_summaries: list[LanguageSummary] = field(default_factory=list)
    top_symbols_by_span: list[tuple[str, str, int, str]] = field(default_factory=list)
    skipped_files: list[tuple[str, str]] = field(default_factory=list)
    total_symbols: int = 0
