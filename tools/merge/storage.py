"""配置文件读写。"""

from __future__ import annotations

import json
import os

from models import MergeConfig

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "merge_config.json")
HISTORY_LIMIT = 9


def load_config() -> MergeConfig:
    if not os.path.exists(CONFIG_FILE):
        return MergeConfig()
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return MergeConfig.from_json_data(json.load(f))
    except Exception as e:
        print(f"⚠️ 配置文件读取失败: {e}")
        return MergeConfig()


def save_config(config: MergeConfig) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config.to_json_dict(), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 配置文件保存失败: {e}")


def add_to_history(history: list[str], path: str) -> list[str]:
    if path in history:
        history.remove(path)
    history.insert(0, path)
    return history[:HISTORY_LIMIT]


def print_history(history: list[str]) -> None:
    if not history:
        print("(无历史记录)")
        return
    print("\n📝 历史路径记忆：")
    for idx, p in enumerate(history, 1):
        print(f"  {idx}. {p}")
    print("")


def print_help() -> None:
    print("\n【merge 工具指令说明】")
    print("  help      : 显示本帮助信息")
    print("  m         : 显示历史记忆的路径列表")
    print("  1-9       : 直接切换到对应历史路径")
    print("  ll        : 列出当前路径下的所有文件夹")
    print("  this      : 切换是否合并子文件夹（仅当前目录 ⇄ 含子目录）")
    print("  r         : 进入持续合并模式（每次回车合并，q 退出循环）")
    print("  q         : 退出程序")
    print("  绝对路径  : 以盘符开头（如 D:\\xxx），切换到指定绝对路径")
    print("  \\相对路径 : 以 \\ 或 / 开头，切换到当前路径下的子文件夹（支持模糊匹配，仅最后一级可模糊）")
    print("  回车      : 执行合并操作 (基于当前路径)")
    print("")
    print("  mod a <组名> <.cs> <.txt> ... : 新增类型组")
    print("  mod u <组名>                : 切换当前类型组")
    print("  mod ll                      : 列出所有类型组")
    print("  mod ll now                  : 查看当前类型组后缀")
    print("  mod d <组名>                : 删除类型组")
    print("")
    print("  exc a <组名> <词1> <词2> ... : 新增排除组（默认区分大小写）")
    print("  exc d <组名>                : 删除排除组")
    print("  exc u <组名>                : 切换当前排除组（仅此时启用）")
    print("  exc q                       : 退出排除模式")
    print("  exc ll                      : 列出所有排除组")
    print("  exc case <组名> <on|off>    : 设置组是否区分大小写")
    print("  exc                         : 启用上次合并成功时的排除组")
    print("")
    print("  c                           : 开关 c 模式（点名合并；关闭时清空选择）")
    print("  c ll                        : 列出 mod+exc 候选（带序号，需已开启 c 模式）")
    print("  c <编号...>                 : 累加选择，如 c 3 5 7")
    print("  c s <编号...>               : 取消已选；单独 c s 显示用法")
    print("  c all / c s all             : 全选 / 取消全选")
    print("  c limit <N>                 : 设置候选列表上限（c 模式下，持久化，默认 50）")
    print("  c limit                     : 查看当前 c limit（c 模式下）")
    print("  回车 (c 模式)               : 仅合并已选文件")
