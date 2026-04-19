import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "merge_config.json")
HISTORY_LIMIT = 9

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
    print("\n【merge 工具指令说明】")
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
