"""交互式 REPL：会话状态 + 主循环（薄层，只做编排）。"""

from __future__ import annotations

import os
from datetime import datetime

from actions import Action
from choose_handlers import (
    handle_choose,
    invalidate_choose_state,
    print_choose_selected_line,
)
from command_handlers import handle_mod
from exc_handlers import handle_exc
from input_parser import parse_input
from merge_engine import run_merge
from merge_report import (
    print_merge_summary,
    print_scan_banner,
    write_merged_output,
)
from path_switch import switch_absolute, switch_relative
from path_tools import get_desktop_path, list_directories
from scope_handlers import handle_this, invalidate_scope_on_path_change
from scope_rules import format_saved_scope_hint, format_scope_for_header
from session import build_run_options
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
        self.this_mode = False
        self.choose_list: list[str] | None = None
        self.choose_selected: set[int] = set()
        self._depth_include_warned = False

    def _scope_text(self) -> str:
        exc = tuple(self.config.merge_scope_exclude)
        inc = tuple(self.config.merge_scope_include)
        if not self.config.scope_enabled:
            saved = format_saved_scope_hint(
                self.config.merge_max_depth, exc, inc
            )
            if saved != "无":
                return f"未启用（已保存: {saved}；输入 this 启用）"
            return "未启用（不限目录范围）"
        return format_scope_for_header(
            self.current_path,
            self.config.merge_max_depth,
            exc,
            inc,
        )

    def _invalidate_choose(self, reason: str = "") -> None:
        if not (
            self.choose_list is not None or self.choose_selected
        ):
            return
        invalidate_choose_state(self)
        if self.choose_mode and reason:
            print(f"ℹ️ c 模式候选已清空（{reason}），请重新输入 c ll 列出。")

    def _invalidate_scope(self, reason: str = "") -> None:
        had_rules = bool(
            self.config.merge_scope_exclude or self.config.merge_scope_include
        )
        invalidate_scope_on_path_change(self.config)
        self._depth_include_warned = False
        save_config(self.config)
        if had_rules and reason:
            print(f"ℹ️ 目录范围细则已清空（{reason}）。")
        self._invalidate_choose(reason)

    def _print_status_header(self) -> None:
        print("-" * 30)
        print(f"📁 当前路径为: {self.current_path}")
        print(
            r"💡 输入 'D:\...' 盘符开头绝对路径 '\相对路径' 修改当前路径 (支持模糊)"
        )
        hint = "回车执行或合并"
        if self.choose_mode:
            hint = "回车合并已选文件 (c 模式)"
        print(
            f"💡 输入 help 查看所有指令, q 退出, {hint}, this/exc 开关范围与排除"
        )
        mod_str = self.config.current_type_group
        exc_str = self.config.current_exclude_group
        parts = [f"当前mod: {mod_str}"]
        if self.this_mode:
            parts.append(f"范围: {self._scope_text()}")
        if exc_str:
            parts.append(f"exc: {exc_str}")
        if self.config.use_gitignore:
            parts.append("gitignore: 开")
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
                print(
                    "❌ c 模式下未选择任何文件。请 c <编号> 或 c all，"
                    "或 c 关闭点名模式后全量合并。"
                )
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
        options = build_run_options(
            self, output_path, only_relative_paths=only_paths
        )
        try:
            if self.config.use_gitignore:
                from gitignore_support import (
                    GitIgnoreMatcher,
                    find_git_root,
                    pathspec_available,
                )

                if not pathspec_available():
                    print(
                        "❌ .gitignore 需要 pathspec 库。请执行: "
                        "pip install -r tools/merge/requirements.txt"
                    )
                    return False
                if find_git_root(self.current_path) is None:
                    print(
                        "⚠️ 已开启 gitignore，但当前路径不在 Git 仓库内，"
                        "将忽略 .gitignore 规则。"
                    )
                elif GitIgnoreMatcher.load(self.current_path) is None:
                    print("⚠️ 未能加载 .gitignore 规则。")
            print_scan_banner(self.current_path, self._scope_text())
            result = run_merge(options)
            print_merge_summary(result, options.file_types)
            write_merged_output(output_path, result)
            self.config.history = add_to_history(
                list(self.config.history), self.current_path
            )
            self.config.last_success_type_group = self.config.current_type_group
            if self.config.current_exclude_group:
                self.config.last_exclude_group = self.config.current_exclude_group
            self.config.last_success_exclude_group = self.config.current_exclude_group
            save_config(self.config)
            print(f"\n✅ 合并完成，文件已生成: {output_path}\n")
            return not self.continuous_mode
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            input("\n按回车键继续...")
            return False

    def run(self) -> None:
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
                if action == Action.THIS:
                    handle_this(self, payload)
                    continue
                if action == Action.THIS_INVALID:
                    print("❌ this 指令格式错误。输入 help 查看说明。")
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
                    self._invalidate_scope("已切换路径")
                    continue
                if action == Action.MOD:
                    handle_mod(payload, self.config)
                    self._invalidate_choose("已修改类型组")
                    continue
                if action == Action.EXC:
                    handle_exc(self, payload)
                    continue
                if action == Action.EXC_INVALID:
                    print("❌ exc 指令格式错误。输入 help 查看 exc 说明。")
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
                    self._invalidate_scope("已切换路径")
                    continue
                if action == Action.SWITCH_REL:
                    self.current_path = switch_relative(
                        payload, self.current_path
                    )
                    self._invalidate_scope("已切换路径")
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
