"""mod / exc 子命令：直接修改 MergeConfig 并持久化。"""

from __future__ import annotations

from typing import Any

from actions import Action
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


def handle_exc(action: Action, payload: Any, config: MergeConfig) -> None:
    if action == Action.EXC_LAST:
        last_exc = config.last_success_exclude_group
        if last_exc and last_exc in config.exclude_groups:
            config.current_exclude_group = last_exc
            save_config(config)
            print(f"✅ 已启用排除组: {last_exc}")
        else:
            print("❌ 没有可用的上次排除组。")
        return
    if action == Action.EXC_ADD:
        group_name, words = payload
        if not words:
            print("❌ 请输入要添加的排除词。")
        else:
            config.exclude_groups[group_name] = {
                "words": words,
                "case_sensitive": True,
            }
            save_config(config)
            print(f"✅ 已添加排除组 '{group_name}': {', '.join(words)} (区分大小写)")
        return
    if action == Action.EXC_DEL:
        group_name = payload
        if group_name in config.exclude_groups:
            del config.exclude_groups[group_name]
            if config.current_exclude_group == group_name:
                config.current_exclude_group = None
            save_config(config)
            print(f"✅ 已删除排除组: {group_name}")
        else:
            print(f"❌ 排除组 '{group_name}' 不存在。")
        return
    if action == Action.EXC_USE:
        group_name = payload
        if group_name in config.exclude_groups:
            config.current_exclude_group = group_name
            save_config(config)
            print(f"✅ 已切换当前排除组为: {group_name}")
        else:
            print(f"❌ 排除组 '{group_name}' 不存在。")
        return
    if action == Action.EXC_DISABLE:
        if config.current_exclude_group:
            old = config.current_exclude_group
            config.current_exclude_group = None
            save_config(config)
            print(f"✅ 已关闭当前排除组: {old}")
        else:
            print("ℹ️ 当前没有开启的排除组。")
        return
    if action == Action.EXC_LIST:
        if not config.exclude_groups:
            print("(无排除组)")
        else:
            print("\n🛑 排除组列表：")
            for k, v in config.exclude_groups.items():
                cs = "区分大小写" if v.get("case_sensitive", True) else "不区分大小写"
                print(f"  {k}: {', '.join(v['words'])} ({cs})")
        return
    if action == Action.EXC_CASE:
        group_name, mode = payload
        mode = mode.lower()
        if group_name in config.exclude_groups:
            if mode == "on":
                config.exclude_groups[group_name]["case_sensitive"] = True
                save_config(config)
                print(f"✅ 排除组 '{group_name}' 已设置为区分大小写")
            elif mode == "off":
                config.exclude_groups[group_name]["case_sensitive"] = False
                save_config(config)
                print(f"✅ 排除组 '{group_name}' 已设置为不区分大小写")
            else:
                print("❌ 只支持 on/off")
        else:
            print(f"❌ 排除组 '{group_name}' 不存在。")
