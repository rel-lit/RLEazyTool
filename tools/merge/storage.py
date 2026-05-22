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
    print("\n【merge 基础】")
    print("  help      : 显示本帮助信息")
    print("  m         : 显示历史记忆的路径列表")
    print("  1-9       : 直接切换到对应历史路径")
    print("  ll        : 列出当前路径下的所有文件夹")
    print("  r         : 进入持续合并模式（每次回车合并，q 退出循环）")
    print("  q         : 退出程序")
    print("  绝对路径  : 以盘符开头（如 D:\\xxx），切换到指定绝对路径")
    print("  \\相对路径 : 以 \\ 或 / 开头，切换到当前路径下的子文件夹（支持模糊匹配，仅最后一级可模糊）")
    print("  回车      : 执行合并操作 (基于当前路径)")
    print("")
    print("【目录范围 this】（仅作用于当前合并根目录；与 mod/exc 独立）")
    print("  this      : 开关配置模式（进入后启用已保存范围；退出后合并不再应用，设置仍保留）")
    print("  this 0    : 仅本层文件（深度 0，任意时刻可设）")
    print("  this N    : 合并时最多扫到深度 N（N≥1）")
    print("  this max  : 取消深度限制（不限深度）")
    print("  this ll     : 列出第 0 层文件夹（等同 this ll 0，带选中标记）")
    print("  this ll N  : 列出第 N 层文件夹（需已开启 this 配置模式）")
    print("  this ll all: 列出整棵目录树可配置节点（需已开启 this 配置模式）")
    print("  this a <路径>: 添加细则包含（多级路径；需已开启 this 配置模式）")
    print("  this s <路径>: 排除子路径（不可排除顶层文件夹；需已开启 this 配置模式）")
    print("")
    print("【类型组 mod】")
    print("  mod a <组名> <.cs> <.txt> ... : 新增类型组")
    print("  mod u <组名>                : 切换当前类型组")
    print("  mod ll                      : 列出所有类型组")
    print("  mod ll now                  : 查看当前类型组后缀")
    print("  mod d <组名>                : 删除类型组")
    print("")
    print("【排除模板 exc】（全局，任意当前路径；设置持久保存）")
    print("  exc           : 开关排除（关闭后再开恢复上次使用的组）")
    print("  exc u <组名>  : 启用指定排除组")
    print("  exc a <组名> | exc d <组名>  : 新建空组 / 删除组")
    print("  exc ll | exc ll now         : 列出所有组 / 当前组详情")
    print("  exc dir a|d|clr|ll <组名>   : 跳过目录名（全局，任意层级）")
    print("  exc f a <组名> <kind> <pattern> : 文件名规则")
    print("       kind: contains prefix suffix glob regex")
    print("  exc f d|clr|ll <组名> ...   : 删规则(序号或kind+pattern) / 清空 / 列出")
    print("  exc gitignore on|off      : 按仓库 .gitignore 排除（自动使用项目 .venv）")
    print("  exc gitignore             : 以 exc 排除语义列出 .gitignore 规则明细")
    print("")
    print("【语法分析 ana】（默认粗略；开则 tree-sitter 符号级分析）")
    print("  ana           : 开关详细语法分析（.venv 自动装依赖）")
    print("  ana show      : 查看分析模式与 tree-sitter 状态")
    print("")
    print("【点名合并 c】")
    print("  c                           : 开关 c 模式（点名合并；关闭时清空选择）")
    print("  c ll                        : 列出 mod+exc 候选（带序号，需已开启 c 模式）")
    print("  c <编号...>                 : 累加选择，如 c 3 5 7")
    print("  c s <编号...>               : 取消已选；单独 c s 显示用法")
    print("  c all / c s all             : 全选 / 取消全选")
    print("  c limit <N>                 : 设置候选列表上限（c 模式下，持久化，默认 50）")
    print("  c limit                     : 查看当前 c limit（c 模式下）")
    print("  回车 (c 模式)               : 仅合并已选文件")
