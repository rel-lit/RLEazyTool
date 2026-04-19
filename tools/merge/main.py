import os
from datetime import datetime
from config_manager import load_config, save_config, add_to_history, print_history, print_help
from path_utils import get_desktop_path, list_directories, find_best_match
from merge_logic import merge_files_by_types
from utils import get_real_path, print_type_groups


def main():
    config = load_config()
    if 'last_success_type_group' in config:
        config['current_type_group'] = config['last_success_type_group']
    history = config.get('history', [])
    current_path = history[0] if history else os.path.dirname(os.path.abspath(__file__))
    first_run = True
    relative_switch_count = 0
    relative_switch_joked = set()
    joke_state = {}
    while True:
        print("-" * 30)
        print(f"📁 当前路径为: {current_path}")
        print("💡 输入 'D:\...' 盘符开头绝对路径 '\相对路径' 修改当前路径 (支持模糊)")
        print("💡 输入 help 查看所有指令, q 退出, 回车执行或合并, 默认基于当前路径")
        if first_run:
            print(f"当前mod: {config.get('current_type_group', 'default')}")
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
            try:
                merge_files_by_types(current_path, output_path, file_types, joke_state=joke_state)
                config['history'] = add_to_history(config.get('history', []), current_path)
                config['last_success_type_group'] = config.get('current_type_group', 'default')
                save_config(config)
                return
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                input("\n按回车键继续...")
            continue
        print(f"⚠️ 无效指令: '{user_input}'")
        print("   请输入路径跳转，或回车执行合并。")

if __name__ == "__main__":
    main()
