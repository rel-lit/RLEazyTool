"""路径切换（绝对 / 相对 + 模糊）。"""

from __future__ import annotations

import os

from path_tools import find_best_match, get_real_path


def switch_absolute(target_folder: str, current_path: str) -> str:
    real_path = get_real_path(target_folder)
    if os.path.exists(real_path) and os.path.isdir(real_path):
        print(f"✅ 已切换到绝对路径: {real_path}")
        return real_path
    print(f"❌ 错误: 绝对路径不存在 -> {target_folder}")
    return current_path


def switch_relative(target_folder: str, current_path: str) -> str:
    relative_part = target_folder.lstrip("\\/")
    direct_path = os.path.normpath(os.path.join(current_path, relative_part))
    real_path = get_real_path(direct_path)
    if os.path.exists(real_path) and os.path.isdir(real_path):
        print(f"✅ 已切换路径至: {real_path}")
        return real_path
    if "\\" not in relative_part and "/" not in relative_part:
        folder_name = relative_part
        best = find_best_match(current_path, folder_name)
        if best:
            matched_path = os.path.join(current_path, best)
            new_path = get_real_path(matched_path)
            print(f"🔍 未找到 '{folder_name}'，已自动修正为: '{best}'")
            print(f"✅ 已切换路径至: {new_path}")
            return new_path
        print(f"❌ 路径不存在，且未找到相似的文件夹: '{relative_part}'")
        return current_path
    print(f"❌ 路径不存在: {direct_path}")
    return current_path
