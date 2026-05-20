"""交互式 REPL：会话状态 + 主循环（薄层，只做编排）。"""

from __future__ import annotations

import os
from datetime import datetime

from actions import Action
from choose_handlers import (
    handle_choose,
    invalidate_choose_state,
    merge_options_from_repl,
    print_choose_selected_line,
)
from command_handlers import handle_exc, handle_mod
from input_parser import parse_input
from merge_engine import MergeRunOptions, run_merge
from merge_report import (
    print_merge_summary,
    print_scan_banner,
    write_merged_output,
)
from path_switch import switch_absolute, switch_relative
from path_tools import get_desktop_path, list_directories
from storage import add_to_history, load_config, print_help, print_history, save_config


class MergeRepl:
    def __init__(self) -> None:
        self.config = load_config()
        if self.config.last_success_type_group:
            self.config.current_type_group = self.config.last_success_type_group
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.current_path = (
            self.config.history[0] if self.config.history else script_dir
        )
        self.first_run = True
        self.continuous_mode = False
        self.choose_mode = False
        self.choose_list: list[str] | None = None
        self.choose_selected: set[int] = set()

    def _invalidate_choose(self, reason: str = "") -> None:
        if not (
            self.choose_list is not None or self.choose_selected
        ):
            return
        invalidate_choose_state(self)
        if self.choose_mode and reason:
            print(f"ℹ️ c 模式候选已清空（{reason}），请重新输入 c ll 列出。")

    def _print_status_header(self) -> None:
        print("-" * 30)
        print(f"📁 当前路径为: {self.current_path}")
        print(
            r"💡 输入 'D:\...' 盘符开头绝对路径 '\相对路径' 修改当前路径 (支持模糊)"
        )
        hint = "回车执行或合并"
        if self.choose_mode:
            hint = "回车合并已选文件 (c 模式)"
        print(f"💡 输入 help 查看所有指令, q 退出, {hint}, this 切换是否含子文件夹")
        mod_str = self.config.current_type_group
        exc_str = self.config.current_exclude_group
        scope_str = "含子目录" if self.config.merge_subfolders else "仅本层"
        parts = [f"当前mod: {mod_str}", f"范围: {scope_str}"]
        if exc_str:
            parts.append(f"exc: {exc_str}")
        if self.choose_mode:
            c_part = (
                f"c: 已选 {len(self.choose_selected)} 个 | limit: {self.config.c_limit}"
            )
            print("📋 " + c_part + " | " + " | ".join(parts))
            print_choose_selected_line(self)
        else:
            print("📋 " + " | ".join(parts))
        if self.first_run:
            print_history(self.config.history)
            self.first_run = False

    def _merge(self) -> bool:
        """执行合并。返回 True 表示应退出 REPL（非持续模式）。"""
        if not os.path.exists(self.current_path):
            print(f"❌ 错误: 当前路径已失效 -> {self.current_path}")
            return False

        only_paths: tuple[str, ...] | None = None
        if self.choose_mode:
            if not self.choose_selected:
                print("❌ c 模式下未选择任何文件。请 c <编号> 或 c all，或 c 关闭点名模式后全量合并。")
                return False
            if self.choose_list is None:
                print("❌ 请先输入 c ll 列出候选，再选择编号。")
                return False
            rels = []
            for idx in sorted(self.choose_selected):
                if 1 <= idx <= len(self.choose_list):
                    rels.append(self.choose_list[idx - 1])
            if not rels:
                print("❌ 所选编号无效，请重新 c 列出并选择。")
                return False
            only_paths = tuple(rels)

        desktop_dir = get_desktop_path()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = os.path.basename(self.current_path) or "Unknown"
        output_filename = f"{folder_name}_MergedFiles_{timestamp}.txt"
        output_path = os.path.join(desktop_dir, output_filename)
        file_types, case_sensitive, exclude_words = merge_options_from_repl(self)
        options = MergeRunOptions(
            source_dir=self.current_path,
            output_path=output_path,
            file_types=tuple(file_types),
            exclude_words=tuple(exclude_words),
            case_sensitive=case_sensitive,
            recursive=self.config.merge_subfolders,
            only_relative_paths=only_paths,
        )
        try:
            print_scan_banner(self.current_path, self.config.merge_subfolders)
            result = run_merge(options)
            print_merge_summary(result, options.file_types)
            write_merged_output(output_path, result)
            self.config.history = add_to_history(
                list(self.config.history), self.current_path
            )
            self.config.last_success_type_group = self.config.current_type_group
            self.config.last_success_exclude_group = self.config.current_exclude_group
            save_config(self.config)
            print(f"✅ 合并完成: {output_path}\n")
            return not self.continuous_mode
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            input("\n按回车键继续...")
            return False

    def run(self) -> None:
        exc_actions = frozenset(
            {
                Action.EXC_LAST,
                Action.EXC_ADD,
                Action.EXC_DEL,
                Action.EXC_USE,
                Action.EXC_DISABLE,
                Action.EXC_LIST,
                Action.EXC_CASE,
            }
        )
        try:
            while True:
                self._print_status_header()
                user_input = input("👉 请输入指令: ").strip()
                action, payload = parse_input(
                    user_input, len(self.config.history)
                )

                if action == Action.QUIT:
                    print("👋 已退出程序。")
                    return
                if action == Action.HELP:
                    print_help()
                    continue
                if action == Action.HISTORY:
                    print_history(self.config.history)
                    continue
                if action == Action.LIST_DIRS:
                    list_directories(self.current_path)
                    continue
                if action == Action.TOGGLE_MERGE_SCOPE:
                    self.config.merge_subfolders = not self.config.merge_subfolders
                    save_config(self.config)
                    if self.config.merge_subfolders:
                        print("✅ 合并范围: 含子文件夹")
                    else:
                        print("✅ 合并范围: 仅当前文件夹（不进入子目录）")
                    self._invalidate_choose("已切换合并范围")
                    continue
                if action == Action.CONTINUOUS_MODE:
                    self.continuous_mode = True
                    print(
                        "\n🔁 已进入持续合并模式：合并后不会自动退出，输入 q 可随时退出。\n"
                    )
                    continue
                if action == Action.SWITCH_HISTORY:
                    self.current_path = self.config.history[payload]
                    print(f"✅ 已切换到历史路径: {self.current_path}")
                    self._invalidate_choose("已切换路径")
                    continue
                if action == Action.MOD:
                    handle_mod(payload, self.config)
                    self._invalidate_choose("已修改类型组")
                    continue
                if action in exc_actions:
                    handle_exc(action, payload, self.config)
                    self._invalidate_choose("已修改排除组")
                    continue
                if action == Action.EXC_INVALID:
                    print("❌ exc 指令格式错误。用法: exc a/u/d/ll/case ...")
                    continue
                if action == Action.CHOOSE:
                    handle_choose(self, payload)
                    continue
                if action == Action.CHOOSE_INVALID:
                    print("❌ c 指令格式错误。输入 help 查看 c 模式说明。")
                    continue
                if action == Action.SWITCH_ABS:
                    self.current_path = switch_absolute(
                        payload, self.current_path
                    )
                    self._invalidate_choose("已切换路径")
                    continue
                if action == Action.SWITCH_REL:
                    self.current_path = switch_relative(
                        payload, self.current_path
                    )
                    self._invalidate_choose("已切换路径")
                    continue
                if action == Action.MERGE:
                    if self._merge():
                        return
                    continue
                if action == Action.INVALID:
                    print(f"⚠️ 无效指令: '{payload}'")
                    print("   请输入路径跳转，或回车执行合并。")
                    continue
                print(f"⚠️ 未处理的指令 action={action!r}，请报告开发者。")
        except KeyboardInterrupt:
            print("\n👋 已中断退出。")


def run_repl() -> None:
    MergeRepl().run()


def main() -> None:
    run_repl()


if __name__ == "__main__":
    main()
