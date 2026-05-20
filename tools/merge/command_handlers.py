"""mod 子命令：直接修改 MergeConfig 并持久化。"""

from __future__ import annotations

from typing import Any

from models import MergeConfig
from path_tools import print_type_groups
from storage import save_config


def handle_mod(parts: list[str], config: MergeConfig) -> None:
    if len(parts) == 3 and parts[1] == "ll" and parts[2] == "now":
        current = config.current_type_group
        exts = config.type_groups.get(current, [])
        print(f"\n⭐ 当前类型组: {current}: {', '.join(exts)}\n")
        return
    if len(parts) >= 3 and parts[1] == "a":
        group_name = parts[2]
        exts = [x if x.startswith(".") else f".{x}" for x in parts[3:]]
        if not exts:
            print("❌ 请输入要添加的文件类型后缀，如 .cs .txt")
        else:
            config.type_groups[group_name] = exts
            save_config(config)
            print(f"✅ 已添加类型组 '{group_name}': {', '.join(exts)}")
        return
    if len(parts) == 3 and parts[1] == "u":
        group_name = parts[2]
        if group_name in config.type_groups:
            config.current_type_group = group_name
            save_config(config)
            print(f"✅ 已切换当前类型组为: {group_name}")
        else:
            print(f"❌ 类型组 '{group_name}' 不存在。")
        return
    if len(parts) == 3 and parts[1] == "d":
        group_name = parts[2]
        if group_name == "default":
            print("❌ 默认类型组不能删除。")
        elif group_name in config.type_groups:
            del config.type_groups[group_name]
            if config.current_type_group == group_name:
                config.current_type_group = "default"
                save_config(config)
                print(f"✅ 已删除类型组: {group_name}，已切换为默认类型组。")
            else:
                save_config(config)
                print(f"✅ 已删除类型组: {group_name}")
        else:
            print(f"❌ 类型组 '{group_name}' 不存在。")
        return
    if len(parts) == 2 and parts[1] == "ll":
        print_type_groups(config.type_groups, config.current_type_group)
        return
    print("❌ Mod 指令格式错误。用法: mod a/u/d/ll ...")
