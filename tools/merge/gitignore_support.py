"""读取仓库 .gitignore 并在扫描时排除匹配路径。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterator

_pathspec_module = None
_pathspec_bootstrap_note: str = ""


def _get_pathspec():
    global _pathspec_module
    if _pathspec_module is not None:
        return _pathspec_module
    try:
        import pathspec as ps

        _pathspec_module = ps
    except ImportError:
        pass
    return _pathspec_module


def pathspec_available() -> bool:
    global _pathspec_bootstrap_note
    if _get_pathspec() is not None:
        return True
    from venv_bootstrap import ensure_pathspec

    ok, note = ensure_pathspec(quiet=True)
    if note:
        _pathspec_bootstrap_note = note
    if ok:
        _pathspec_module = None
        return _get_pathspec() is not None
    return False


def consume_pathspec_bootstrap_note() -> str:
    global _pathspec_bootstrap_note
    note = _pathspec_bootstrap_note
    _pathspec_bootstrap_note = ""
    return note


def find_git_root(start_dir: str) -> str | None:
    path = os.path.abspath(start_dir)
    while True:
        if os.path.isdir(os.path.join(path, ".git")):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent


def _read_pattern_lines(gitignore_path: str) -> list[str]:
    lines: list[str] = []
    try:
        with open(gitignore_path, encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                lines.append(line)
    except OSError:
        pass
    return lines


def _iter_gitignore_files(repo_root: str) -> Iterator[tuple[str, str]]:
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        if ".gitignore" not in filenames:
            continue
        yield dirpath, os.path.join(dirpath, ".gitignore")


def collect_gitignore_patterns(repo_root: str) -> list[str]:
    """合并仓库内所有 .gitignore（含子目录），规则相对仓库根路径。"""
    patterns: list[str] = []
    repo_root = os.path.abspath(repo_root)
    for dirpath, gi_path in _iter_gitignore_files(repo_root):
        rel_dir = os.path.relpath(dirpath, repo_root)
        if rel_dir == ".":
            prefix = ""
        else:
            prefix = rel_dir.replace("\\", "/") + "/"
        for line in _read_pattern_lines(gi_path):
            if line.startswith("!"):
                body = line[1:].lstrip()
                neg = "!"
            else:
                body = line
                neg = ""
            if body.startswith("/"):
                pat = neg + prefix + body[1:]
            else:
                pat = neg + prefix + body
            patterns.append(pat)
    return patterns


@dataclass(frozen=True)
class GitIgnoreFileRules:
    rel_path: str
    patterns: tuple[str, ...]


@dataclass(frozen=True)
class ExcStyleIgnoreRule:
    raw: str
    exc_kind: str
    label: str


def describe_gitignore_as_exc(line: str) -> ExcStyleIgnoreRule:
    """将 .gitignore 一行译为与 exc 相近的排除/包含语义。"""
    if line.startswith("!"):
        body = line[1:].lstrip()
        return ExcStyleIgnoreRule(
            raw=line,
            exc_kind="include",
            label=f"细则包含（例外，不排除） → {body}",
        )
    if line.endswith("/"):
        name = line.rstrip("/")
        return ExcStyleIgnoreRule(
            raw=line,
            exc_kind="dir",
            label=f"跳过目录/树（类似 exc dir） → {name}",
        )
    if "/" in line and not line.startswith("*"):
        return ExcStyleIgnoreRule(
            raw=line,
            exc_kind="path",
            label=f"排除路径前缀 → {line}",
        )
    if any(c in line for c in "*?[]"):
        return ExcStyleIgnoreRule(
            raw=line,
            exc_kind="glob",
            label=f"文件名 glob（类似 exc f glob） → {line}",
        )
    return ExcStyleIgnoreRule(
        raw=line,
        exc_kind="match",
        label=f"排除匹配 → {line}",
    )


def describe_resolved_as_exc(pattern: str) -> str:
    if pattern.startswith("!"):
        return f"细则包含（例外） → {pattern[1:]}"
    if pattern.endswith("/"):
        return f"跳过目录/树 → {pattern}"
    if "/" in pattern:
        return f"排除路径 → {pattern}"
    if any(c in pattern for c in "*?[]"):
        return f"glob 排除 → {pattern}"
    return f"排除 → {pattern}"


def collect_gitignore_by_file(repo_root: str) -> list[GitIgnoreFileRules]:
    repo_root = os.path.abspath(repo_root)
    groups: list[GitIgnoreFileRules] = []
    for dirpath, gi_path in _iter_gitignore_files(repo_root):
        rel = os.path.relpath(gi_path, repo_root).replace("\\", "/")
        patterns = tuple(_read_pattern_lines(gi_path))
        if patterns:
            groups.append(GitIgnoreFileRules(rel_path=rel, patterns=patterns))
    return groups


def build_gitignore_report(
    source_dir: str,
    *,
    filter_enabled: bool,
    per_file_limit: int = 60,
    resolved_limit: int = 80,
) -> list[str]:
    """生成 exc gitignore 明细：以 exc 排除语义描述 .gitignore 规则。"""
    lines: list[str] = [
        "[exc gitignore] 合并扫描时的排除（读取 .gitignore，全局生效）",
        f"  开关: {'开' if filter_enabled else '关'}",
        "  语义: 命中下列规则的文件/目录不会进入合并（等同 exc 全局过滤，非 exc 模板组）",
    ]
    note = consume_pathspec_bootstrap_note()
    if note:
        lines.append(f"  ℹ️ {note}")

    if not pathspec_available():
        lines.append("  状态: 无法加载 pathspec，请检查项目 .venv。")
        return lines

    lines.append("  状态: pathspec 已就绪")
    root = find_git_root(source_dir)
    if root is None:
        lines.append("  当前路径不在 Git 仓库内，合并时 .gitignore 不生效。")
        return lines

    groups = collect_gitignore_by_file(root)
    resolved = collect_gitignore_patterns(root)
    raw_total = sum(len(g.patterns) for g in groups)
    lines.append(f"  仓库根: {root}")
    lines.append(
        f"  汇总: {len(groups)} 个 .gitignore，原始 {raw_total} 条 → "
        f"合并解析后 {len(resolved)} 条排除规则"
    )
    if not groups and not resolved:
        lines.append("  （无有效规则）")
        return lines

    if groups:
        lines.append("")
        lines.append("  ── 按源文件（exc 语义）──")
        for group in groups:
            n = len(group.patterns)
            lines.append(f"  来源 [{group.rel_path}]（{n} 条）")
            for raw in group.patterns[:per_file_limit]:
                desc = describe_gitignore_as_exc(raw)
                lines.append(f"    · {desc.label}")
            if n > per_file_limit:
                lines.append(f"    … 还有 {n - per_file_limit} 条未列出")
            lines.append("")

    if resolved:
        lines.append("  ── 合并后实际参与匹配（相对仓库根）──")
        for pat in resolved[:resolved_limit]:
            lines.append(f"    · {describe_resolved_as_exc(pat)}")
        if len(resolved) > resolved_limit:
            lines.append(f"    … 还有 {len(resolved) - resolved_limit} 条未列出")

    if lines and lines[-1] == "":
        lines.pop()
    return lines


@dataclass(frozen=True)
class GitIgnoreMatcher:
    repo_root: str
    pattern_count: int
    _spec: object

    @classmethod
    def load(cls, source_dir: str) -> GitIgnoreMatcher | None:
        ps = _get_pathspec()
        if ps is None and not pathspec_available():
            return None
        ps = _get_pathspec()
        if ps is None:
            return None
        root = find_git_root(source_dir)
        if root is None:
            return None
        patterns = collect_gitignore_patterns(root)
        spec = ps.PathSpec.from_lines("gitwildmatch", patterns)
        return cls(repo_root=root, pattern_count=len(patterns), _spec=spec)

    def ignores_file(self, abs_path: str) -> bool:
        rel = os.path.relpath(abs_path, self.repo_root).replace("\\", "/")
        return bool(self._spec.match_file(rel))  # type: ignore[union-attr]

    def ignores_dir(self, abs_dir: str) -> bool:
        rel = os.path.relpath(abs_dir, self.repo_root).replace("\\", "/")
        if not rel.endswith("/"):
            rel += "/"
        return bool(self._spec.match_file(rel))  # type: ignore[union-attr]
