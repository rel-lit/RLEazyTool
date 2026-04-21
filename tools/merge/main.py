import os
from datetime import datetime
from config_manager import load_config, save_config, add_to_history, print_history, print_help
from path_utils import get_desktop_path, list_directories, find_best_match
from merge_logic import merge_files_by_types
from utils import get_real_path, print_type_groups


def main():
    config = load_config()
    # 强制初始化：不自动恢复上次的排除组和类型组
    config['current_exclude_group'] = None  # 核心修改：强制默认为 None
    if 'last_success_type_group' in config:
        config['current_type_group'] = config['last_success_type_group']
    history = config.get('history', [])
    current_path = history[0] if history else os.path.dirname(os.path.abspath(__file__))
    first_run = True
    relative_switch_count = 0
    relative_switch_joked = set()
    joke_state = {}
    continuous_mode = False
    while True:
        print("-" * 30)
        print(f"📁 当前路径为: {current_path}")
        print("💡 输入 'D:\...' 盘符开头绝对路径 '\相对路径' 修改当前路径 (支持模糊)")
        print("💡 输入 help 查看所有指令, q 退出, 回车执行或合并, 默认基于当前路径")
        # 显示当前mod和exc排除组
        mod_str = config.get('current_type_group', 'default')
        exc_str = config.get('current_exclude_group')
        if exc_str:
            print(f"当前mod: {mod_str} | exc: {exc_str}")
        else:
            print(f"当前mod: {mod_str}")
        if first_run:
            print_history(config.get('history', []))
            first_run = False
        user_input = input("👉 请输入指令: ").strip()
        # --- Mod 指令 ---
        if user_input.lower().startswith('mod '):
            parts = user_input.strip().split()
            if len(parts) == 3 and parts[1] == 'll' and parts[2] == 'now':
                current = config.get('current_type_group', 'default')
                exts = config['type_groups'].get(current, [])
                print(f"\n⭐ 当前类型组: {current}: {', '.join(exts)}\n")
                continue
            if len(parts) >= 3 and parts[1] == 'a':
                group_name = parts[2]
                exts = [x if x.startswith('.') else f'.{x}' for x in parts[3:]]
                if not exts:
                    print("❌ 请输入要添加的文件类型后缀，如 .cs .txt")
                else:
                    config['type_groups'][group_name] = exts
                    save_config(config)
                    print(f"✅ 已添加类型组 '{group_name}': {', '.join(exts)}")
                continue
            if len(parts) == 3 and parts[1] == 'u':
                group_name = parts[2]
                if group_name in config['type_groups']:
                    config['current_type_group'] = group_name
                    save_config(config)
                    print(f"✅ 已切换当前类型组为: {group_name}")
                else:
                    print(f"❌ 类型组 '{group_name}' 不存在。")
                continue
            if len(parts) == 3 and parts[1] == 'd':
                group_name = parts[2]
                if group_name == 'default':
                    print("❌ 默认类型组不能删除。")
                elif group_name in config['type_groups']:
                    del config['type_groups'][group_name]
                    if config['current_type_group'] == group_name:
                        config['current_type_group'] = 'default'
                        save_config(config)
                        print(f"✅ 已删除类型组: {group_name}，已切换为默认类型组。")
                    else:
                        save_config(config)
                        print(f"✅ 已删除类型组: {group_name}")
                else:
                    print(f"❌ 类型组 '{group_name}' 不存在。")
                continue
            if len(parts) == 2 and parts[1] == 'll':
                print_type_groups(config['type_groups'], config['current_type_group'])
                continue
            print("❌ Mod 指令格式错误。用法: mod a/u/d/ll ...")
            continue
        # --- Exc 指令 ---
        if user_input.lower().startswith('exc'):
            parts = user_input.strip().split()
            if len(parts) == 1:
                # exc: 直接启用上次合并成功的排除组
                last_exc = config.get('last_success_exclude_group')
                if last_exc and last_exc in config['exclude_groups']:
                    config['current_exclude_group'] = last_exc
                    save_config(config)
                    print(f"✅ 已启用排除组: {last_exc}")
                else:
                    print("❌ 没有可用的上次排除组。")
                continue
            if len(parts) >= 3 and parts[1] == 'a':
                group_name = parts[2]
                words = parts[3:]
                if not words:
                    print("❌ 请输入要添加的排除词。")
                else:
                    config['exclude_groups'][group_name] = {"words": words, "case_sensitive": True}
                    save_config(config)
                    print(f"✅ 已添加排除组 '{group_name}': {', '.join(words)} (区分大小写)")
                continue
            if len(parts) == 3 and parts[1] == 'd':
                group_name = parts[2]
                if group_name in config['exclude_groups']:
                    del config['exclude_groups'][group_name]
                    if config.get('current_exclude_group') == group_name:
                        config['current_exclude_group'] = None
                    save_config(config)
                    print(f"✅ 已删除排除组: {group_name}")
                else:
                    print(f"❌ 排除组 '{group_name}' 不存在。")
                continue
            if len(parts) == 3 and parts[1] == 'u':
                group_name = parts[2]
                if group_name in config['exclude_groups']:
                    config['current_exclude_group'] = group_name
                    save_config(config)
                    print(f"✅ 已切换当前排除组为: {group_name}")
                else:
                    print(f"❌ 排除组 '{group_name}' 不存在。")
                continue
            if len(parts) == 2 and parts[1] == 'q': # exc q 指令
                if config.get('current_exclude_group'):
                    old_name = config['current_exclude_group']
                    config['current_exclude_group'] = None
                    save_config(config)
                    print(f"✅ 已关闭当前排除组: {old_name}")
                else:
                    print("ℹ️ 当前没有开启的排除组。")
                continue
            if len(parts) == 2 and parts[1] == 'll':
                if not config['exclude_groups']:
                    print("(无排除组)")
                else:
                    print("\n🛑 排除组列表：")
                    for k, v in config['exclude_groups'].items():
                        cs = '区分大小写' if v.get('case_sensitive', True) else '不区分大小写'
                        print(f"  {k}: {', '.join(v['words'])} ({cs})")
                continue
            if len(parts) == 4 and parts[1] == 'case':
                group_name = parts[2]
                mode = parts[3].lower()
                if group_name in config['exclude_groups']:
                    if mode == 'on':
                        config['exclude_groups'][group_name]['case_sensitive'] = True
                        save_config(config)
                        print(f"✅ 排除组 '{group_name}' 已设置为区分大小写")
                    elif mode == 'off':
                        config['exclude_groups'][group_name]['case_sensitive'] = False
                        save_config(config)
                        print(f"✅ 排除组 '{group_name}' 已设置为不区分大小写")
                    else:
                        print("❌ 只支持 on/off")
                else:
                    print(f"❌ 排除组 '{group_name}' 不存在。")
                continue
            print("❌ exc 指令格式错误。用法: exc a/u/d/ll/case ...")
            continue
        # 其它指令
        if user_input.lower() == 'q':
            print("👋 已退出程序。")
            return
        if user_input.lower() == 'help':
            print_help()
            continue
        if user_input.lower() == 'm':
            print_history(config.get('history', []))
            continue
        if user_input.lower() == 'll':
            list_directories(current_path)
            continue
        if user_input.isdigit() and 1 <= int(user_input) <= len(config.get('history', [])):
            idx = int(user_input) - 1
            current_path = config['history'][idx]
            print(f"✅ 已切换到历史路径: {current_path}")
            continue
        if user_input.lower() == 'r':
            continuous_mode = True
            print("\n🔁 已进入持续合并模式：合并后不会自动退出，输入 q 可随时退出。\n")
            continue
        # 路径切换逻辑
        target_folder = user_input
        if target_folder.startswith('"') and target_folder.endswith('"'):
            target_folder = target_folder[1:-1]
        if ":" in target_folder:
            real_path = get_real_path(target_folder)
            if os.path.exists(real_path) and os.path.isdir(real_path):
                current_path = real_path
                print(f"✅ 已切换到绝对路径: {current_path}")
            else:
                print(f"❌ 错误: 绝对路径不存在 -> {target_folder}")
            continue
        if target_folder.startswith('\\') or target_folder.startswith('/'):
            relative_part = target_folder.lstrip('\\/')
            direct_path = os.path.normpath(os.path.join(current_path, relative_part))
            real_path = get_real_path(direct_path)
            relative_switch_count += 1
            if relative_switch_count == 3 and 3 not in relative_switch_joked:
                print("路径切换第3次啦，你不会已经迷路了吧？要不要美少女来带路呀~")
                relative_switch_joked.add(3)
            if relative_switch_count == 5 and 5 not in relative_switch_joked:
                print("都切换5次了，你是不是在考验我的耐心？屑气美少女可是不会轻易认输的！")
                relative_switch_joked.add(5)
            if relative_switch_count == 8 and 8 not in relative_switch_joked:
                print("8次路径切换，迷宫小能手认证！要不要我给你发个小红花？")
                relative_switch_joked.add(8)
            if os.path.exists(real_path) and os.path.isdir(real_path):
                current_path = real_path
                print(f"✅ 已切换路径至: {current_path}")
                continue
            if '\\' not in relative_part and '/' not in relative_part:
                folder_name = relative_part
                best_match_name = find_best_match(current_path, folder_name)
                if best_match_name:
                    matched_path = os.path.join(current_path, best_match_name)
                    current_path = get_real_path(matched_path)
                    print(f"🔍 未找到 '{folder_name}'，已自动修正为: '{best_match_name}'")
                    print(f"✅ 已切换路径至: {current_path}")
                    continue
                else:
                    print(f"❌ 路径不存在，且未找到相似的文件夹: '{relative_part}'")
                    continue
            else:
                print(f"❌ 路径不存在: {direct_path}")
                continue
        # 合并操作
        if user_input == "":
            if not os.path.exists(current_path):
                print(f"❌ 错误: 当前路径已失效 -> {current_path}")
                continue
            desktop_dir = get_desktop_path()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = os.path.basename(current_path) or "Unknown"
            output_filename = f"{folder_name}_MergedFiles_{timestamp}.txt"
            output_path = os.path.join(desktop_dir, output_filename)
            file_types = config['type_groups'].get(config.get('current_type_group', 'default'), ['.cs'])
            # 获取当前排除组
            exclude_words = []
            case_sensitive = True
            exc_group = config.get('current_exclude_group')
            if exc_group and exc_group in config['exclude_groups']:
                exclude_words = config['exclude_groups'][exc_group]['words']
                case_sensitive = config['exclude_groups'][exc_group].get('case_sensitive', True)
            try:
                merge_files_by_types(current_path, output_path, file_types, joke_state=joke_state, exclude_words=exclude_words, case_sensitive=case_sensitive)
                config['history'] = add_to_history(config.get('history', []), current_path)
                config['last_success_type_group'] = config.get('current_type_group', 'default')
                # 记录本次成功的排除组
                config['last_success_exclude_group'] = config.get('current_exclude_group')
                save_config(config)
                print(f"✅ 合并完成: {output_path}\n")
                if not continuous_mode:
                    return
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                input("\n按回车键继续...")
            continue
        print(f"⚠️ 无效指令: '{user_input}'")
        print("   请输入路径跳转，或回车执行合并。")

if __name__ == "__main__":
    main()
