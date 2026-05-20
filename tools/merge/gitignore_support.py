"""读取仓库 .gitignore 并在扫描时排除匹配路径。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterator

try:
    import pathspec
except ImportError:
    pathspec = None  # type: ignore[assignment]


def pathspec_available() -> bool:
    return pathspec is not None


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
class GitIgnoreMatcher:
    repo_root: str
    pattern_count: int
    _spec: object

    @classmethod
    def load(cls, source_dir: str) -> GitIgnoreMatcher | None:
        if pathspec is None:
            return None
        root = find_git_root(source_dir)
        if root is None:
            return None
        patterns = collect_gitignore_patterns(root)
        spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        return cls(repo_root=root, pattern_count=len(patterns), _spec=spec)

    def ignores_file(self, abs_path: str) -> bool:
        rel = os.path.relpath(abs_path, self.repo_root).replace("\\", "/")
        return bool(self._spec.match_file(rel))  # type: ignore[union-attr]

    def ignores_dir(self, abs_dir: str) -> bool:
        rel = os.path.relpath(abs_dir, self.repo_root).replace("\\", "/")
        if not rel.endswith("/"):
            rel += "/"
        return bool(self._spec.match_file(rel))  # type: ignore[union-attr]
