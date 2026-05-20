"""合并目录范围：最大深度、顶层文件夹默认全选、多级 include/exclude。"""

from __future__ import annotations

import os

from dataclasses import dataclass

from constants import EXCLUDE_DIR_NAMES


@dataclass(frozen=True)
class ScopeContext:
    source_dir: str
    max_depth: int | None
    scope_exclude: tuple[str, ...]
    scope_include: tuple[str, ...]
    top_level_dirs: frozenset[str]

    @classmethod
    def create(
        cls,
        source_dir: str,
        max_depth: int | None,
        scope_exclude: tuple[str, ...] = (),
        scope_include: tuple[str, ...] = (),
    ) -> ScopeContext:
        return cls(
            source_dir=source_dir,
            max_depth=max_depth,
            scope_exclude=scope_exclude,
            scope_include=scope_include,
            top_level_dirs=frozenset(list_top_level_dir_names(source_dir)),
        )


def norm_rel_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def file_depth(relative_path: str) -> int:
    rel = norm_rel_path(relative_path)
    if not rel:
        return 0
    return rel.count("/")


def min_file_depth_under_prefix(prefix: str) -> int:
    """该路径前缀下任意文件的最小深度。"""
    p = norm_rel_path(prefix)
    if not p:
        return 0
    return p.count("/") + 1


def list_top_level_dir_names(source_dir: str) -> list[str]:
    names: list[str] = []
    try:
        for name in sorted(os.listdir(source_dir)):
            p = os.path.join(source_dir, name)
            if os.path.isdir(p):
                names.append(name)
    except OSError:
        pass
    return names


def list_folder_nodes_at_layer(source_dir: str, layer: int) -> list[str]:
    if layer < 0:
        return []
    if layer == 0:
        return list_top_level_dir_names(source_dir)
    found: set[str] = set()
    try:
        for root, dirs, _files in os.walk(source_dir):
            rel_root = os.path.relpath(root, source_dir)
            if rel_root == ".":
                rel_root = ""
            rel_root = norm_rel_path(rel_root)
            depth = 0 if not rel_root else rel_root.count("/") + 1
            if depth != layer:
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIR_NAMES]
            for d in dirs:
                if rel_root:
                    found.add(f"{rel_root}/{d}")
                else:
                    found.add(d)
    except OSError:
        pass
    return sorted(found)


def iter_all_folder_nodes(source_dir: str) -> list[str]:
    nodes: list[str] = []
    for name in list_top_level_dir_names(source_dir):
        nodes.append(name)
    try:
        for root, dirs, _files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIR_NAMES]
            rel_root = os.path.relpath(root, source_dir)
            if rel_root == ".":
                continue
            rel_root = norm_rel_path(rel_root)
            nodes.append(rel_root)
    except OSError:
        pass
    return sorted(set(nodes))


def is_top_level_folder_path(path: str) -> bool:
    p = norm_rel_path(path)
    return bool(p) and "/" not in p


def _path_under_prefix(rel_path: str, prefix: str) -> bool:
    rel = norm_rel_path(rel_path)
    p = norm_rel_path(prefix)
    if not p:
        return False
    return rel == p or rel.startswith(p + "/")


def file_in_merge_scope(relative_path: str, ctx: ScopeContext) -> bool:
    rel = norm_rel_path(relative_path)
    depth = file_depth(rel)

    if ctx.max_depth is not None and depth > ctx.max_depth:
        return False

    if depth == 0:
        return True

    top = rel.split("/")[0]
    if top not in ctx.top_level_dirs:
        return False

    for exc in ctx.scope_exclude:
        if _path_under_prefix(rel, exc):
            for inc in ctx.scope_include:
                if _path_under_prefix(rel, inc):
                    return True
            return False

    for inc in ctx.scope_include:
        if _path_under_prefix(rel, inc):
            return True

    return True


def format_scope_for_header(
    source_dir: str,
    max_depth: int | None,
    scope_exclude: tuple[str, ...],
    scope_include: tuple[str, ...],
) -> str:
    if max_depth == 0:
        return "仅本层（深度 0 文件）"
    tops = list_top_level_dir_names(source_dir)
    if max_depth is None:
        head = f"不限深度；顶层 {len(tops)} 个文件夹默认纳入"
    else:
        head = f"最大深度 {max_depth}；顶层 {len(tops)} 个文件夹默认纳入"
    parts = [head]
    if scope_exclude:
        parts.append("排除: " + ", ".join(scope_exclude[:8]))
        if len(scope_exclude) > 8:
            parts.append("…")
    if scope_include:
        parts.append("细则: " + ", ".join(scope_include[:8]))
    return "；".join(parts)


def folder_marker(
    folder_path: str,
    scope_exclude: tuple[str, ...],
    scope_include: tuple[str, ...],
    *,
    is_top_level: bool,
) -> str:
    p = norm_rel_path(folder_path)
    if is_top_level:
        return "[*]"
    for exc in scope_exclude:
        if _path_under_prefix(p, exc):
            if not any(_path_under_prefix(p, inc) for inc in scope_include):
                return "[-]"
    for inc in scope_include:
        if _path_under_prefix(p, inc):
            return "[+]"
    return "[ ]"
