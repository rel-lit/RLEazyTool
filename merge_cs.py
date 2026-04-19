import os
import sys
import json
import winreg
import re
from datetime import datetime

CONFIG_FILE = "merge_config.json"

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

def load_last_path():
    """加载上次的路径"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get('last_path')
        except:
            return None
    return None

def save_last_path(path):
    """保存当前路径 (仅在合并成功时调用)"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({'last_path': path}, f)
    except:
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
            if (i + 1) % 3 == 0: print() # 每3个换行
        print("\n") # 结尾补个空行
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
        
        target_lower = target_name.lower()
        
        # 用于存储所有包含关键词的文件夹
        containing_matches = []
        
        # --- 【分段模糊匹配】 ---
        partial_matches = []

        for d in dirs:
            d_lower = d.lower()
            
            # 【逻辑 1】检查完整包含关系
            if target_lower in d_lower:
                containing_matches.append(d)
            
            # 【逻辑 2】检查分段匹配
            else:
                # 将文件夹名按驼峰或下划线分割
                parts = split_camel_case(d)
                for part in parts:
                    # 计算输入词与文件夹某一部分的编辑距离
                    distance = levenshtein_distance(target_lower, part)
                    # 如果距离很小（允许错1个字母），就认为是匹配的
                    if distance <= 1:
                        partial_matches.append(d)
                        break # 只要匹配上一部分就行
                
                # 如果没有分段匹配，再计算整体编辑距离
                if d not in partial_matches:
                    distance = levenshtein_distance(target_lower, d_lower)
                    # 动态阈值
                    dir_count = len(dirs)
                    if dir_count <= 5:
                        threshold = 3 
                    elif dir_count <= 10:
                        threshold = 2
                    else:
                        threshold = 1
                    
                    if distance <= threshold and distance < min_distance:
                        min_distance = distance
                        best_match = d
        
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
        return best_match
        
    except:
        return None

def merge_cs_files(source_dir, output_path):
    """核心合并逻辑"""
    exclude_dirs = {'.git', 'bin', 'obj', 'node_modules', '.vs', 'packages', 'Debug', 'Release'}
    file_count = 0
    error_count = 0

    print(f"🔍 正在扫描目录: {source_dir}")
    with open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.write(f"// 合并时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        outfile.write(f"// 来源目录: {source_dir}\n")
        outfile.write(f"// ==========================================\n")

        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.cs'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, source_dir)
                    outfile.write(f"\n\n// ==================== 文件: {relative_path} ====================\n\n")
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            content = infile.read()
                        outfile.write(content)
                        file_count += 1
                    except Exception as e:
                        outfile.write(f"// [错误] 无法读取文件: {e}\n")
                        error_count += 1

    return file_count, error_count

def main():
    print("--- C# 代码合并工具 (智能版) ---")
    
    # 1. 初始化路径
    current_path = load_last_path()
    if not current_path:
        current_path = os.path.dirname(os.path.abspath(__file__))
    
    # 辅助函数：获取真实大小写路径
    def get_real_path(path):
        if os.path.exists(path):
            return os.path.realpath(path)
        return path

    while True:
        # 2. 显示当前状态
        print("-" * 30)
        print(f"📁 当前路径为: {current_path}")
        print("💡 输入 'D:\\...' 盘符开头绝对路径, '\\相对路径' 修改当前路径 (支持模糊)")
        print("💡 输入 ll 列出当前路径文件夹, q 退出, 回车执行或合并, 默认基于当前路径")
        
        # 3. 获取输入
        user_input = input("👉 请输入指令: ").strip()

        # 4. 退出逻辑
        if user_input.lower() == 'q':
            print("👋 已退出程序。")
            return

        # 5. 列出目录指令 (ll)
        if user_input.lower() == 'll':
            list_directories(current_path)
            continue

        # 6. 路径切换逻辑
        target_folder = user_input
        
        # 去除引号
        if target_folder.startswith('"') and target_folder.endswith('"'):
            target_folder = target_folder[1:-1]

        # 情况 A: 绝对路径 (包含盘符:)
        if ":" in target_folder:
            real_path = get_real_path(target_folder)
            if os.path.exists(real_path) and os.path.isdir(real_path):
                current_path = real_path
                print(f"✅ 已切换到绝对路径: {current_path}")
            else:
                print(f"❌ 错误: 绝对路径不存在 -> {target_folder}")
            continue

        # 情况 B: 相对路径 (以 \ 或 / 开头) -> 【加入了模糊匹配】
        if target_folder.startswith('\\') or target_folder.startswith('/'):
            # 去掉开头的斜杠，获取纯文件夹名
            relative_part = target_folder.lstrip('\\/')
            
            # 1. 先尝试精确匹配 (拼接完整路径)
            direct_path = os.path.normpath(os.path.join(current_path, relative_part))
            real_path = get_real_path(direct_path)
            
            if os.path.exists(real_path) and os.path.isdir(real_path):
                current_path = real_path
                print(f"✅ 已切换路径至: {current_path}")
                continue
            
            # 2. 如果精确匹配失败，且输入的内容不包含子路径，则尝试模糊匹配
            if '\\' not in relative_part and '/' not in relative_part:
                # 提取最后一级目录名进行模糊匹配
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
                 # 如果是复杂路径，精确匹配失败就直接报错
                 print(f"❌ 路径不存在: {direct_path}")
                 continue

        # 情况 C: 执行合并 (直接回车)
        if user_input == "":
            if not os.path.exists(current_path):
                print(f"❌ 错误: 当前路径已失效 -> {current_path}")
                continue

            desktop_dir = get_desktop_path()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = os.path.basename(current_path) or "Unknown"
            output_filename = f"{folder_name}_MergedCsCode_{timestamp}.txt"
            output_path = os.path.join(desktop_dir, output_filename)

            try:
                count, errors = merge_cs_files(current_path, output_path)
                print("-" * 30)
                print(f"✅ 成功! 共处理了 {count} 个 .cs 文件。")
                if errors > 0:
                    print(f"⚠️ 有 {errors} 个文件读取失败。")
                print(f"📄 结果已保存至: {output_path}")
                
                save_last_path(current_path)
                return 
                
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                input("\n按回车键继续...")
            continue

        # 情况 D: 无效指令
        print(f"⚠️ 无效指令: '{user_input}'")
        print("   请输入路径跳转，或回车执行合并。")

if __name__ == "__main__":
    main()