"""C# 源码粗统计（全文件正则 + 按类型体解析）；修复了原先循环内覆盖 method_count 的 bug。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class RunningCsStats:
    class_count: int = 0
    struct_count: int = 0
    enum_count: int = 0
    interface_count: int = 0
    variable_count: int = 0
    method_count: int = 0
    # (is_abstract_class, is_interface, name, body_lines, methods, fields, abstract_methods)
    cs_class_infos: list[tuple] = field(default_factory=list)
    enum_member_counts: list[int] = field(default_factory=list)
    struct_field_counts: list[int] = field(default_factory=list)


_re_class = re.compile(r"\bclass\s+\w+")
_re_struct = re.compile(r"\bstruct\s+\w+")
_re_enum = re.compile(r"\benum\s+\w+")
_re_interface = re.compile(r"\binterface\s+\w+")
_re_variable = re.compile(
    r"\b(public|private|protected|internal)\s+((static|readonly|const|volatile|sealed|virtual|override|new)\s+)*"
    r"[\w<>\[\],]+\s+\w+\s*(=|;|\{)"
)
_re_method = re.compile(
    r"\b(public|private|protected|internal)\s+((static|virtual|override|async|sealed|new|partial)\s+)*"
    r"[\w<>\[\],]+\s+\w+\s*\([^;]*\)\s*(\{|where|$)"
)
_class_pattern = re.compile(
    r"(public|private|protected|internal)?\s*(abstract)?\s*class\s+(\w+)"
)
_interface_pattern = re.compile(
    r"(public|private|protected|internal)?\s*interface\s+(\w+)"
)
_struct_pattern = re.compile(
    r"(public|private|protected|internal)?\s*struct\s+(\w+)"
)
_enum_pattern = re.compile(
    r"(public|private|protected|internal)?\s*enum\s+(\w+)"
)


def _extract_type_body(content: str, start_idx: int) -> str:
    brace = 0
    in_body = False
    body: list[str] = []
    for i in range(start_idx, len(content)):
        c = content[i]
        if c == "{":
            brace += 1
            in_body = True
        if in_body:
            body.append(c)
        if c == "}":
            brace -= 1
            if brace == 0 and in_body:
                break
    return "".join(body)


def analyze_cs_content(stats: RunningCsStats, content: str) -> None:
    """累加单文件统计到 stats（可多次调用合并多文件）。"""
    stats.class_count += len(_re_class.findall(content))
    stats.struct_count += len(_re_struct.findall(content))
    stats.enum_count += len(_re_enum.findall(content))
    stats.interface_count += len(_re_interface.findall(content))
    stats.variable_count += len(_re_variable.findall(content))
    stats.method_count += len(_re_method.findall(content))

    for m in _class_pattern.finditer(content):
        is_abstract = m.group(2) is not None
        class_name = m.group(3)
        class_body = _extract_type_body(content, m.start())
        methods = re.findall(
            r"(public|private|protected|internal)?\s*(abstract)?\s*([\w<>,\[\]]+)\s+(\w+)\s*\([^;{)]*\)\s*(;|\{)",
            class_body,
        )
        n_methods = len(methods)
        fields = re.findall(
            r"(public|private|protected|internal)\s+((static|readonly|const|volatile|sealed|virtual|override|new)\s+)*"
            r"[\w<>,\[\]]+\s+\w+\s*(=|;|\{)",
            class_body,
        )
        field_count = len(fields)
        abstract_methods = [x for x in methods if x[1] == "abstract"]
        abstract_method_count = len(abstract_methods)
        stats.cs_class_infos.append(
            (
                is_abstract,
                False,
                class_name,
                class_body.count("\n"),
                n_methods,
                field_count,
                abstract_method_count,
            )
        )

    for m in _interface_pattern.finditer(content):
        interface_name = m.group(2)
        interface_body = _extract_type_body(content, m.start())
        methods_iface = re.findall(
            r"([\w<>,\[\]]+)\s+(\w+)\s*\([^;{)]*\)\s*;",
            interface_body,
        )
        n_iface_methods = len(methods_iface)
        stats.cs_class_infos.append(
            (
                False,
                True,
                interface_name,
                interface_body.count("\n"),
                n_iface_methods,
                0,
                0,
            )
        )

    for m in _struct_pattern.finditer(content):
        struct_body = _extract_type_body(content, m.start())
        fields = re.findall(
            r"(public|private|protected|internal)\s+((static|readonly|const|volatile|sealed|virtual|override|new)\s+)*"
            r"[\w<>,\[\]]+\s+\w+\s*(=|;|\{)",
            struct_body,
        )
        stats.struct_field_counts.append(len(fields))

    for m in _enum_pattern.finditer(content):
        enum_body = _extract_type_body(content, m.start())
        members = [
            x
            for x in enum_body.split(",")
            if x.strip() and not x.strip().startswith("//")
        ]
        stats.enum_member_counts.append(len(members))
