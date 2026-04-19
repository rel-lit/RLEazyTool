# 通用工具函数将在此实现

import os

def get_real_path(path):
    """返回路径的真实绝对路径，如果存在"""
    if os.path.exists(path):
        return os.path.realpath(path)
    return path

def print_type_groups(type_groups, current):
    print("\n📦 类型组列表：")
    for name, types in type_groups.items():
        mark = "*" if name == current else " "
        print(f"  {mark} {name}: {', '.join(types)}")
    print("")
