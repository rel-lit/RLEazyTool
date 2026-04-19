import os
import json
import winreg
import re
from datetime import datetime

# 获取当前脚本所在目录，保证 config 文件读写在同一目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "merge_config.json")
HISTORY_LIMIT = 9

def get_desktop_path():
    """使用注册表获取真实的桌面路径"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        )
        desktop_path, _ = winreg.QueryValueEx(key, "Desktop")
        winreg.CloseKey(key)
        return desktop_path
    except Exception:
        return os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')


# --- 配置文件管理 ---
def load_config():
    """加载配置文件，返回 dict，兼容旧格式"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 兼容旧格式
                if isinstance(data, list):
                    return {"history": data, "type_groups": {"default": [".cs"]}, "current_type_group": "default"}
                if isinstance(data, dict):
                    # 填补缺失字段
                    if "history" not in data:
                        data["history"] = []
                    if "type_groups" not in data:
                        data["type_groups"] = {"default": [".cs"]}
                    if "current_type_group" not in data:
                        data["current_type_group"] = "default"
                    return data
        except Exception as e:
            print(f"⚠️ 配置文件读取失败: {e}")
            return {"history": [], "type_groups": {"default": [".cs"]}, "current_type_group": "default"}
    return {"history": [], "type_groups": {"default": [".cs"]}, "current_type_group": "default"}

def save_config(config):
    """保存配置文件（dict）"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 配置文件保存失败: {e}")

def add_to_history(history, path):
    """将新路径加入历史，去重并保持顺序"""
    if path in history:
        history.remove(path)
    history.insert(0, path)
    return history[:HISTORY_LIMIT]

def print_history(history):
    if not history:
        print("(无历史记录)")
        return
    print("\n📝 历史路径记忆：")
    for idx, p in enumerate(history, 1):
        print(f"  {idx}. {p}")
    print("")

def print_help():
    print("\n【merge_cs 工具指令说明】")
    print("  help      : 显示本帮助信息")
    print("  m         : 显示历史记忆的路径列表")
    print("  1-9       : 直接切换到对应历史路径")
    print("  ll        : 列出当前路径下的所有文件夹")
    print("  q         : 退出程序")
    print("  绝对路径  : 以盘符开头（如 D:\\xxx），切换到指定绝对路径")
    print("  \\相对路径 : 以 \\ 或 / 开头，切换到当前路径下的子文件夹（支持模糊匹配，仅最后一级可模糊）")
    print("  回车      : 执行合并操作 (基于当前路径)")
    print("")
    print("  mod a <组名> <.cs> <.txt> ... : 新增类型组")
    print("  mod u <组名>                : 切换当前类型组")
    print("  mod ll                      : 列出所有类型组")
    print("  mod d <组名>                : 删除类型组")
    print("")


def load_last_path():
    """加载上次的路径"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get('last_path')
        except Exception:
            return None
    return None

def save_last_path(path):
    """保存当前路径 (仅在合并成功时调用)"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({'last_path': path}, f)
    except Exception:
        pass

def list_directories(path):
    """列出当前路径下的所有文件夹 (ll 指令)"""
    try:
        items = os.listdir(path)
        dirs = []
        for item in items:
            if os.path.isdir(os.path.join(path, item)):
                dirs.append(item)
        
        print(f"\n📂 当前路径下的文件夹 ({len(dirs)}个):")
        # 简单的分列显示
        for i, d in enumerate(sorted(dirs)):
            print(f"   {d}", end="")
            if (i + 1) % 3 == 0:
                print()  # 每3个换行
        print("\n")  # 结尾补个空行
    except PermissionError:
        print("⚠️ 权限不足，无法列出目录。")
    except Exception as e:
        print(f"❌ 列出目录失败: {e}")

# --- 模糊匹配算法 (计算编辑距离) ---
def levenshtein_distance(s1, s2):
    """计算两个字符串的编辑距离（相似度）"""
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

def split_camel_case(s):
    """将文件夹名分割成单词列表，支持驼峰和下划线"""
    # 1. 先按非字母数字字符（如下划线、横杠、空格）分割
    parts = re.split(r'[^a-zA-Z0-9]', s)
    
    result = []
    for part in parts:
        # 2. 对每一部分再进行驼峰分割
        camel_parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+', part)
        result.extend(camel_parts)
    
    # 3. 转小写并过滤空字符串
    return [w.lower() for w in result if w]

def find_best_match(current_dir, target_name):
    """在当前目录下寻找最匹配的文件夹名"""
    try:
        items = os.listdir(current_dir)
        # 只获取文件夹
        dirs = [item for item in items if os.path.isdir(os.path.join(current_dir, item))]
        
        if not dirs:
            return None

        best_match = None
        min_distance = float('inf')
        
        target_lower = target_name.lower();
        
        # 用于存储所有包含关键词的文件夹
        containing_matches = []
        
        # --- 【分段模糊匹配】 ---
        partial_matches = []

        for d in dirs:
            d_lower = d.lower();
            
            # 【逻辑 1】检查完整包含关系
            if target_lower in d_lower:
                containing_matches.append(d);
            
            # 【逻辑 2】检查分段匹配
            else:
                # 将文件夹名按驼峰或下划线分割
                parts = split_camel_case(d);
                for part in parts:
                    # 计算输入词与文件夹某一部分的编辑距离
                    distance = levenshtein_distance(target_lower, part);
                    # 如果距离很小（允许错1个字母），就认为是匹配的
                    if distance <= 1:
                        partial_matches.append(d);
                        break # 只要匹配上一部分就行
                
                # 如果没有分段匹配，再计算整体编辑距离
                if d not in partial_matches:
                    distance = levenshtein_distance(target_lower, d_lower);
                    # 动态阈值
                    dir_count = len(dirs);
                    if dir_count <= 5:
                        threshold = 3 ;
                    elif dir_count <= 10:
                        threshold = 2;
                    else:
                        threshold = 1;
                    
                    if distance <= threshold and distance < min_distance:
                        min_distance = distance;
                        best_match = d;
        
        # 【防歧义机制】如果包含匹配或分段匹配的结果不止一个，直接返回 None
        if len(containing_matches) > 1:
            return None
        if len(partial_matches) > 1:
            return None
            
        # 如果有且仅有一个包含匹配，优先返回它
        if len(containing_matches) == 1:
            return containing_matches[0]
        
        # 如果有且仅有一个分段匹配，返回它
        if len(partial_matches) == 1:
            return partial_matches[0]
        
        # 如果都没有，返回编辑距离匹配的结果
        return best_match;
        
    except Exception:
        return None

def merge_files_by_types(source_dir, output_path, file_types):
    """支持多类型文件合并，.cs 文件统计 C# 结构，其余类型只统计文件数和行数"""
    exclude_dirs = {'.git', 'bin', 'obj', 'node_modules', '.vs', 'packages', 'Debug', 'Release'}
    file_count = 0
    error_count = 0
    total_lines = 0
    class_count = 0
    struct_count = 0
    enum_count = 0
    interface_count = 0
    variable_count = 0
    method_count = 0
    type_file_count = {ext: 0 for ext in file_types}

    # 正则表达式（仅 .cs 用）
    re_class = re.compile(r'\bclass\s+\w+')
    re_struct = re.compile(r'\bstruct\s+\w+')
    re_enum = re.compile(r'\benum\s+\w+')
    re_interface = re.compile(r'\binterface\s+\w+')
    re_variable = re.compile(r'\b(public|private|protected|internal)\s+((static|readonly|const|volatile|sealed|virtual|override|new)\s+)*[\w<>\[\],]+\s+\w+\s*(=|;|\{)')
    re_method = re.compile(r'\b(public|private|protected|internal)\s+((static|virtual|override|async|sealed|new|partial)\s+)*[\w<>\[\],]+\s+\w+\s*\([^;]*\)\s*(\{|where|$)')

    print(f"🔍 正在扫描目录: {source_dir}")

    # 新增详细结构统计（仅 .cs 文件）
    cs_class_infos = []  # [(is_abstract, is_interface, class_name, class_lines, method_count, field_count, abstract_method_count)]
    enum_member_counts = []
    struct_field_counts = []
    interface_method_counts = []

    def analyze_cs_classes(content):
        nonlocal class_count, struct_count, enum_count, interface_count, variable_count, method_count
        # 统计所有类型
        class_count += len(re_class.findall(content))
        struct_count += len(re_struct.findall(content))
        enum_count += len(re_enum.findall(content))
        interface_count += len(re_interface.findall(content))
        variable_count += len(re_variable.findall(content))
        method_count += len(re_method.findall(content))

        # 逐个类型分析
        # 1. 类和抽象类
        class_pattern = re.compile(r'(public|private|protected|internal)?\s*(abstract)?\s*class\s+(\w+)')
        for m in class_pattern.finditer(content):
            is_abstract = m.group(2) is not None
            class_name = m.group(3)
            # 提取类体
            class_body = extract_type_body(content, m.start())
            # 方法数
            methods = re.findall(r'(public|private|protected|internal)?\s*(abstract)?\s*([\w<>,\[\]]+)\s+(\w+)\s*\([^;{)]*\)\s*(;|\{)', class_body)
            method_count = len(methods)
            # 字段数
            fields = re.findall(r'(public|private|protected|internal)\s+((static|readonly|const|volatile|sealed|virtual|override|new)\s+)*[\w<>,\[\]]+\s+\w+\s*(=|;|\{)', class_body)
            field_count = len(fields)
            # 抽象方法数
            abstract_methods = [m for m in methods if m[1] == 'abstract']
            abstract_method_count = len(abstract_methods)
            cs_class_infos.append((is_abstract, False, class_name, class_body.count('\n'), method_count, field_count, abstract_method_count))

        # 2. 接口
        interface_pattern = re.compile(r'(public|private|protected|internal)?\s*interface\s+(\w+)')
        for m in interface_pattern.finditer(content):
            interface_name = m.group(2)
            interface_body = extract_type_body(content, m.start())
            # 接口方法数
            methods = re.findall(r'([\w<>,\[\]]+)\s+(\w+)\s*\([^;{)]*\)\s*;', interface_body)
            method_count = len(methods)
            cs_class_infos.append((False, True, interface_name, interface_body.count('\n'), method_count, 0, 0))
            interface_method_counts.append(method_count)

        # 3. 结构体
        struct_pattern = re.compile(r'(public|private|protected|internal)?\s*struct\s+(\w+)')
        for m in struct_pattern.finditer(content):
            struct_body = extract_type_body(content, m.start())
            fields = re.findall(r'(public|private|protected|internal)\s+((static|readonly|const|volatile|sealed|virtual|override|new)\s+)*[\w<>,\[\]]+\s+\w+\s*(=|;|\{)', struct_body)
            struct_field_counts.append(len(fields))

        # 4. 枚举
        enum_pattern = re.compile(r'(public|private|protected|internal)?\s*enum\s+(\w+)')
        for m in enum_pattern.finditer(content):
            enum_body = extract_type_body(content, m.start())
            members = [x for x in enum_body.split(',') if x.strip() and not x.strip().startswith('//')]
            enum_member_counts.append(len(members))

    def extract_type_body(content, start_idx):
        # 提取从 start_idx 开始的类型体（{} 包裹部分）
        brace = 0
        in_body = False
        body = []
        for i in range(start_idx, len(content)):
            c = content[i]
            if c == '{':
                brace += 1
                in_body = True
            if in_body:
                body.append(c)
            if c == '}':
                brace -= 1
                if brace == 0 and in_body:
                    break
        return ''.join(body)

    # 先扫描并统计所有内容，收集合并内容
    merged_contents = []
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            for ext in file_types:
                if file.endswith(ext):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, source_dir)
                    merged_contents.append(f"\n\n// ==================== 文件: {relative_path} ====================\n\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            content = infile.read()
                        lines = content.splitlines()
                        total_lines += len(lines)
                        type_file_count[ext] += 1
                        if ext == '.cs':
                            analyze_cs_classes(content)
                        merged_contents.append(content)
                        file_count += 1
                    except Exception as e:
                        merged_contents.append(f"// [错误] 无法读取文件: {e}\n")
                        error_count += 1
                    break  # 一个文件只计一次

    # 构建详细统计字符串 stat_lines（仅用于文件头部）
    merge_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    stat_lines = []
    stat_lines.append(f"// 合并时间: {merge_time}")
    stat_lines.append(f"// 来源目录: {source_dir}")
    main_stat = "// 合并统计：共 {} 个文件，总行数 {}，".format(file_count, total_lines)
    main_stat += ", ".join(["{} 文件 {} 个".format(ext, type_file_count[ext]) for ext in file_types])
    if '.cs' in file_types:
        main_stat += "，类 {} 个，结构体 {} 个，枚举 {} 个，接口 {} 个，变量/字段/属性 {} 个，方法 {} 个".format(
            class_count, struct_count, enum_count, interface_count, variable_count, method_count)
    main_stat += "，读取失败 {} 个文件".format(error_count)
    stat_lines.append(main_stat)

    # 详细统计信息（文件头部专用）
    if '.cs' in file_types:
        real_classes = [c for c in cs_class_infos if not c[0] and not c[1]]
        abstract_classes = [c for c in cs_class_infos if c[0] and not c[1]]
        interfaces = [c for c in cs_class_infos if c[1]]
        avg_real_class_len = round(sum(c[3] for c in real_classes)/len(real_classes), 2) if real_classes else 0
        avg_abstract_methods = round(sum(c[6] for c in abstract_classes)/len(abstract_classes), 2) if abstract_classes else 0
        max_class_len = max((c[3] for c in cs_class_infos), default=0)
        min_class_len = min((c[3] for c in cs_class_infos), default=0)
        avg_methods_per_class = round(sum(c[4] for c in cs_class_infos)/len(cs_class_infos), 2) if cs_class_infos else 0
        avg_fields_per_class = round(sum(c[5] for c in cs_class_infos)/len(cs_class_infos), 2) if cs_class_infos else 0
        avg_enum_members = round(sum(enum_member_counts)/len(enum_member_counts), 2) if enum_member_counts else 0
        avg_struct_fields = round(sum(struct_field_counts)/len(struct_field_counts), 2) if struct_field_counts else 0
        avg_iface_methods = round(sum(c[4] for c in interfaces)/len(interfaces), 2) if interfaces else 0
        stat_lines.append("// [详细统计] 实际类平均长度: {} 行，抽象类平均抽象方法数: {}，最大类长度: {}，最小类长度: {}".format(
            avg_real_class_len, avg_abstract_methods, max_class_len, min_class_len))
        stat_lines.append("// [详细统计] 平均每类方法数: {}，平均每类字段数: {}".format(
            avg_methods_per_class, avg_fields_per_class))
        stat_lines.append("// [详细统计] 枚举平均成员数: {}，结构体平均字段数: {}，接口平均方法数: {}".format(
            avg_enum_members, avg_struct_fields, avg_iface_methods))

    stat_lines.append("// ==========================================")
    stat_str = "\n".join(stat_lines) + "\n"

    # 终端输出（简明摘要，不带注释号，不含详细统计）
    print("-" * 30)
    print(f"✅ 成功! 共处理了 {file_count} 个文件，总行数 {total_lines}。")
    for ext in file_types:
        print(f"   {ext} 文件: {type_file_count[ext]} 个")
    if '.cs' in file_types:
        print(f"   类: {class_count}，结构体: {struct_count}，枚举: {enum_count}，接口: {interface_count}")
        print(f"   变量/字段/属性: {variable_count}，方法: {method_count}")
    if error_count > 0:
        print(f"⚠️ 有 {error_count} 个文件读取失败。")
    print(f"📄 结果已保存至: {output_path}")

    # 写入合并文件，统计信息在最前面
    with open(output_path, 'w', encoding='utf-8') as fout:
        fout.write(stat_str)
        for f in merged_contents:
            fout.write(f)

    return file_count, error_count, total_lines, class_count, struct_count, enum_count, interface_count, variable_count, method_count, type_file_count

def main():
    config = load_config()
    history = config.get('history', [])
    current_path = history[0] if history else os.path.dirname(os.path.abspath(__file__))
    first_run = True
    def get_real_path(path):
        if os.path.exists(path):
            return os.path.realpath(path)
        return path

    def print_type_groups(type_groups, current):
        print("\n📦 类型组列表：")
        for name, types in type_groups.items():
            mark = "*" if name == current else " "
            print(f"  {mark} {name}: {', '.join(types)}")
        print("")

    while True:
        # 2. 显示当前状态
        print("-" * 30)
        print(f"📁 当前路径为: {current_path}")
        print("💡 输入 'D:\\...' 盘符开头绝对路径 '\\相对路径' 修改当前路径 (支持模糊)")
        print("💡 输入 help 查看所有指令, q 退出, 回车执行或合并, 默认基于当前路径")
        if first_run:
            print_history(config.get('history', []))
            first_run = False

        # 3. 获取输入
        user_input = input("👉 请输入指令: ").strip()

        # --- Mod 指令 ---
        if user_input.lower().startswith('mod '):
            parts = user_input.strip().split()
            # 新增 mod ll now
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

        # 4. 指令处理
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
                result = merge_files_by_types(current_path, output_path, file_types)
                file_count, errors, total_lines, class_count, struct_count, enum_count, interface_count, variable_count, method_count, type_file_count = result
                print("-" * 30)
                print(f"✅ 成功! 共处理了 {file_count} 个文件，总行数 {total_lines}。")
                for ext in file_types:
                    print(f"   {ext} 文件: {type_file_count[ext]} 个")
                if '.cs' in file_types:
                    print(f"   类: {class_count}，结构体: {struct_count}，枚举: {enum_count}，接口: {interface_count}")
                    print(f"   变量/字段/属性: {variable_count}，方法: {method_count}")
                if errors > 0:
                    print(f"⚠️ 有 {errors} 个文件读取失败。")
                print(f"📄 结果已保存至: {output_path}")
                # 更新历史
                config['history'] = add_to_history(config.get('history', []), current_path)
                save_config(config)
                return
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                input("\n按回车键继续...")
            continue

        # 无效指令
        print(f"⚠️ 无效指令: '{user_input}'")
        print("   请输入路径跳转，或回车执行合并。")

if __name__ == "__main__":
    main()