"""后缀 → tree-sitter 语言模块名。"""

from __future__ import annotations

# 值: pip 包 import 名（见 analysis/tree_loader.py）
EXT_TO_LANGUAGE: dict[str, str | None] = {
    ".cs": "c_sharp",
    ".py": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".mod": "go",
    ".java": "java",
    ".kt": "java",
    ".kts": "java",
    ".rs": "rust",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "cpp",
    ".hpp": "cpp",
    ".c": "cpp",
    ".php": "php",
    ".rb": "ruby",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "css",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".vue": "html",
    # 配置/工程文件：详细模式无 AST，仅粗略统计
    ".csproj": None,
    ".sln": None,
    ".props": None,
    ".targets": None,
    ".xml": None,
    ".ini": None,
    ".toml": None,
    ".txt": None,
    ".rst": None,
    ".env": None,
    ".env.example": None,
}


def language_for_ext(ext: str) -> str | None:
    return EXT_TO_LANGUAGE.get(ext.lower())
