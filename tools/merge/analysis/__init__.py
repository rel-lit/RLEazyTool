"""源码合并后的分析：粗略（默认）+ 详细（ana 开关，tree-sitter）。"""

from .pipeline import aggregate_project, analyze_file_detailed
from .report import build_detailed_analysis_lines
from .tree_loader import tree_sitter_available

__all__ = [
    "analyze_file_detailed",
    "aggregate_project",
    "build_detailed_analysis_lines",
    "tree_sitter_available",
]
