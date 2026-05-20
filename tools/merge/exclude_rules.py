"""exc 模板：跳过目录名 + 文件名规则（全局，不区分大小写）。"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from typing import Any

from constants import EXCLUDE_DIR_NAMES

FILE_RULE_KINDS = frozenset({"contains", "prefix", "suffix", "glob", "regex"})


@dataclass(frozen=True)
class FileExcludeRule:
    kind: str
    pattern: str


def empty_exclude_group() -> dict[str, Any]:
    return {"skip_dirs": [], "file_rules": []}


def normalize_exclude_group(raw: Any) -> dict[str, Any]:
    """旧配置 words[] 迁移为 file_rules contains。"""
    if not isinstance(raw, dict):
        return empty_exclude_group()
    if "file_rules" in raw or "skip_dirs" in raw:
        skip_dirs = [norm_skip_dir(x) for x in (raw.get("skip_dirs") or [])]
        rules: list[dict[str, str]] = []
        for item in raw.get("file_rules") or []:
            if not isinstance(item, dict):
                continue
            kind = str(item.get("kind", "")).lower()
            pattern = str(item.get("pattern", ""))
            if kind in FILE_RULE_KINDS and pattern:
                rules.append({"kind": kind, "pattern": pattern})
        return {"skip_dirs": _dedupe_list(skip_dirs), "file_rules": rules}
    words = raw.get("words") or []
    rules = [
        {"kind": "contains", "pattern": str(w)}
        for w in words
        if str(w).strip()
    ]
    return {"skip_dirs": [], "file_rules": rules}


def file_rules_from_group(group: dict[str, Any]) -> tuple[FileExcludeRule, ...]:
    return tuple(
        FileExcludeRule(kind=r["kind"], pattern=r["pattern"])
        for r in group.get("file_rules") or []
        if isinstance(r, dict) and r.get("kind") in FILE_RULE_KINDS
    )


def skip_dirs_from_group(group: dict[str, Any]) -> tuple[str, ...]:
    return tuple(group.get("skip_dirs") or [])


def walk_skip_dir_names(exc_skip_dirs: tuple[str, ...]) -> frozenset[str]:
    return frozenset(EXCLUDE_DIR_NAMES) | frozenset(exc_skip_dirs)


def norm_skip_dir(name: str) -> str:
    return name.replace("\\", "/").strip("/")


def filename_excluded(file_name: str, rules: tuple[FileExcludeRule, ...]) -> bool:
    if not rules:
        return False
    return any(_rule_matches(file_name, rule) for rule in rules)


def _rule_matches(file_name: str, rule: FileExcludeRule) -> bool:
    pattern = rule.pattern
    if rule.kind == "contains":
        return pattern.lower() in file_name.lower()
    if rule.kind == "prefix":
        return file_name.lower().startswith(pattern.lower())
    if rule.kind == "suffix":
        return file_name.lower().endswith(pattern.lower())
    if rule.kind == "glob":
        return fnmatch.fnmatch(file_name.lower(), pattern.lower())
    if rule.kind == "regex":
        try:
            return re.search(pattern, file_name) is not None
        except re.error:
            return False
    return False


def _dedupe_list(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out
