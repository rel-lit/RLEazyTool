"""路径相关：桌面、规范化路径、列目录、模糊匹配文件夹。"""

from __future__ import annotations

import os
import re
import winreg


def get_real_path(path: str) -> str:
    if os.path.exists(path):
        return os.path.realpath(path)
    return path


def get_desktop_path() -> str:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
        )
        desktop_path, _ = winreg.QueryValueEx(key, "Desktop")
        winreg.CloseKey(key)
        return desktop_path
    except Exception:
        return os.path.join(os.environ["USERPROFILE"], "Desktop")


def list_directories(path: str) -> None:
    try:
        items = os.listdir(path)
        dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
        print(f"\n📂 当前路径下的文件夹 ({len(dirs)}个):")
        for i, d in enumerate(sorted(dirs)):
            print(f"   {d}", end="")
            if (i + 1) % 3 == 0:
                print()
        print("\n")
    except PermissionError:
        print("⚠️ 权限不足，无法列出目录。")
    except Exception as e:
        print(f"❌ 列出目录失败: {e}")


def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def split_camel_case(s: str) -> list[str]:
    parts = re.split(r"[^a-zA-Z0-9]", s)
    result: list[str] = []
    for part in parts:
        camel_parts = re.findall(
            r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+", part
        )
        result.extend(camel_parts)
    return [w.lower() for w in result if w]


def find_best_match(current_dir: str, target_name: str) -> str | None:
    try:
        items = os.listdir(current_dir)
        dirs = [item for item in items if os.path.isdir(os.path.join(current_dir, item))]
        if not dirs:
            return None
        best_match = None
        min_distance = float("inf")
        target_lower = target_name.lower()
        containing_matches: list[str] = []
        partial_matches: list[str] = []
        for d in dirs:
            d_lower = d.lower()
            if target_lower in d_lower:
                containing_matches.append(d)
            else:
                parts_cc = split_camel_case(d)
                for part in parts_cc:
                    distance = levenshtein_distance(target_lower, part)
                    if distance <= 1:
                        partial_matches.append(d)
                        break
                if d not in partial_matches:
                    distance = levenshtein_distance(target_lower, d_lower)
                    dir_count = len(dirs)
                    threshold = 3 if dir_count <= 5 else 2 if dir_count <= 10 else 1
                    if distance <= threshold and distance < min_distance:
                        min_distance = distance
                        best_match = d
        if len(containing_matches) > 1:
            return None
        if len(partial_matches) > 1:
            return None
        if len(containing_matches) == 1:
            return containing_matches[0]
        if len(partial_matches) == 1:
            return partial_matches[0]
        return best_match
    except Exception:
        return None


def print_type_groups(type_groups: dict[str, list[str]], current: str) -> None:
    print("\n📦 类型组列表：")
    for name, types in type_groups.items():
        mark = "*" if name == current else " "
        print(f"  {mark} {name}: {', '.join(types)}")
    print("")
