"""基于 tree-sitter 的 IDE 级符号提取（按语言节点类型映射）。"""

from __future__ import annotations

from typing import Any

from .tree_loader import get_parser
from .types import FileAnalysisResult, SymbolInfo

# node.type → 符号种类（各语言 tree-sitter 语法）
NODE_KIND_MAP: dict[str, dict[str, str]] = {
    "c_sharp": {
        "class_declaration": "class",
        "struct_declaration": "struct",
        "interface_declaration": "interface",
        "enum_declaration": "enum",
        "record_declaration": "record",
        "method_declaration": "method",
        "constructor_declaration": "constructor",
        "property_declaration": "property",
        "field_declaration": "field",
        "event_declaration": "event",
        "delegate_declaration": "delegate",
        "namespace_declaration": "namespace",
        "using_directive": "using",
    },
    "python": {
        "class_definition": "class",
        "function_definition": "function",
        "import_statement": "import",
        "import_from_statement": "import",
    },
    "javascript": {
        "class_declaration": "class",
        "function_declaration": "function",
        "method_definition": "method",
        "lexical_declaration": "variable",
        "import_statement": "import",
        "export_statement": "export",
    },
    "typescript": {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "enum_declaration": "enum",
        "type_alias_declaration": "type",
        "function_declaration": "function",
        "method_definition": "method",
        "import_statement": "import",
        "export_statement": "export",
    },
    "go": {
        "function_declaration": "function",
        "method_declaration": "method",
        "type_declaration": "type",
        "import_declaration": "import",
        "package_clause": "package",
    },
    "java": {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "enum_declaration": "enum",
        "method_declaration": "method",
        "constructor_declaration": "constructor",
        "field_declaration": "field",
        "import_declaration": "import",
        "package_declaration": "package",
    },
    "rust": {
        "struct_item": "struct",
        "enum_item": "enum",
        "trait_item": "trait",
        "impl_item": "impl",
        "function_item": "function",
        "mod_item": "module",
        "use_declaration": "use",
    },
    "cpp": {
        "class_specifier": "class",
        "struct_specifier": "struct",
        "enum_specifier": "enum",
        "function_definition": "function",
        "function_declarator": "function",
        "namespace_definition": "namespace",
        "template_declaration": "template",
    },
    "php": {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "trait_declaration": "trait",
        "function_definition": "function",
        "method_declaration": "method",
        "namespace_definition": "namespace",
    },
    "ruby": {
        "class": "class",
        "module": "module",
        "method": "method",
        "singleton_method": "method",
    },
    "html": {
        "element": "element",
        "script_element": "script",
        "style_element": "style",
    },
    "css": {
        "rule_set": "rule",
        "media_statement": "media",
    },
    "json": {
        "pair": "pair",
    },
    "yaml": {
        "block_mapping_pair": "pair",
    },
    "markdown": {
        "atx_heading": "heading",
        "fenced_code_block": "code_block",
    },
}

IMPORT_NODE_TYPES = frozenset(
    {
        "using_directive",
        "using_statement",
        "import_statement",
        "import_from_statement",
        "import_declaration",
        "use_declaration",
        "import_declaration",
        "package_declaration",
        "package_clause",
    }
)


def _node_name(node: Any, source: bytes) -> str | None:
    for child in node.children:
        if child.type in ("identifier", "name", "type_identifier", "property_identifier"):
            text = source[child.start_byte : child.end_byte].decode(
                "utf-8", errors="replace"
            )
            return text.strip()
        if child.type == "nested_identifier":
            text = source[child.start_byte : child.end_byte].decode(
                "utf-8", errors="replace"
            )
            return text.strip()
    if node.type in ("identifier", "name"):
        return source[node.start_byte : node.end_byte].decode(
            "utf-8", errors="replace"
        ).strip()
    return None


def _line_of(point_row: int) -> int:
    return point_row + 1


def _walk(
    node: Any,
    source: bytes,
    lang_key: str,
    kind_map: dict[str, str],
    symbols: list[SymbolInfo],
    imports: list[str],
    parent_name: str | None,
) -> None:
    kind = kind_map.get(node.type)
    name = _node_name(node, source) if kind else None
    current_parent = parent_name

    if node.type == "decorated_definition":
        for child in node.children:
            _walk(
                child,
                source,
                lang_key,
                kind_map,
                symbols,
                imports,
                parent_name,
            )
        return

    if node.type in IMPORT_NODE_TYPES:
        snippet = source[node.start_byte : node.end_byte].decode(
            "utf-8", errors="replace"
        )
        line = snippet.replace("\n", " ").strip()[:120]
        if line:
            imports.append(line)

    if kind and name:
        sym = SymbolInfo(
            kind=kind,
            name=name,
            line_start=_line_of(node.start_point[0]),
            line_end=_line_of(node.end_point[0]),
            parent=parent_name,
        )
        symbols.append(sym)
        current_parent = name

    for child in node.children:
        _walk(child, source, lang_key, kind_map, symbols, imports, current_parent)


def analyze_with_tree_sitter(
    lang_key: str,
    content: str,
    *,
    relative_path: str,
    ext: str,
) -> FileAnalysisResult:
    parsed = get_parser(lang_key)
    if parsed is None:
        return FileAnalysisResult(
            relative_path=relative_path,
            ext=ext,
            language=lang_key,
            ok=False,
            error=f"未安装 tree-sitter 语法包（{lang_key}）",
        )
    parser, _lang = parsed
    kind_map = NODE_KIND_MAP.get(lang_key, {})
    if not kind_map:
        return FileAnalysisResult(
            relative_path=relative_path,
            ext=ext,
            language=lang_key,
            ok=False,
            error="无符号映射配置",
        )
    source = content.encode("utf-8")
    tree = parser.parse(source)
    symbols: list[SymbolInfo] = []
    imports: list[str] = []
    _walk(tree.root_node, source, lang_key, kind_map, symbols, imports, None)
    return FileAnalysisResult(
        relative_path=relative_path,
        ext=ext,
        language=lang_key,
        ok=True,
        symbols=symbols,
        imports=imports[:50],
    )
