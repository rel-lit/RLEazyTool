"""懒加载 tree-sitter 语法与 Parser。"""

from __future__ import annotations

import importlib
from functools import lru_cache
from typing import Any

_PARSER_CACHE: dict[str, Any] = {}


def tree_sitter_available() -> bool:
    try:
        import tree_sitter  # noqa: F401

        return True
    except ImportError:
        return False


def _import_language_module(lang_key: str):
    """lang_key 见 registry.EXT_TO_LANGUAGE 的值。"""
    module_names = {
        "c_sharp": "tree_sitter_c_sharp",
        "python": "tree_sitter_python",
        "javascript": "tree_sitter_javascript",
        "typescript": "tree_sitter_typescript",
        "go": "tree_sitter_go",
        "java": "tree_sitter_java",
        "rust": "tree_sitter_rust",
        "cpp": "tree_sitter_cpp",
        "php": "tree_sitter_php",
        "ruby": "tree_sitter_ruby",
        "html": "tree_sitter_html",
        "css": "tree_sitter_css",
        "json": "tree_sitter_json",
        "yaml": "tree_sitter_yaml",
        "markdown": "tree_sitter_markdown",
    }
    mod_name = module_names.get(lang_key)
    if not mod_name:
        return None
    try:
        return importlib.import_module(mod_name)
    except ImportError:
        return None


@lru_cache(maxsize=32)
def get_parser(lang_key: str) -> Any | None:
    if not tree_sitter_available():
        from venv_bootstrap import ensure_merge_deps

        ensure_merge_deps(quiet=True)
    if lang_key in _PARSER_CACHE:
        return _PARSER_CACHE[lang_key]
    mod = _import_language_module(lang_key)
    if mod is None:
        from venv_bootstrap import ensure_analysis_extra

        ensure_analysis_extra(quiet=True)
        get_parser.cache_clear()  # type: ignore[attr-defined]
        mod = _import_language_module(lang_key)
    if mod is None:
        return None
    from tree_sitter import Language, Parser

    lang = Language(mod.language())
    parser = Parser(lang)
    _PARSER_CACHE[lang_key] = (parser, lang)
    return _PARSER_CACHE[lang_key]
