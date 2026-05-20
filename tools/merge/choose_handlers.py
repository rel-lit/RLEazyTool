"""c 模式：按编号点名合并（mod+exc 候选列表）。"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from merge_engine import collect_candidate_paths
from session import filter_settings_from_config, scope_settings_from_config
from storage import save_config

if TYPE_CHECKING:
    from repl import MergeRepl


def invalidate_choose_state(repl: "MergeRepl") -> None:
    repl.choose_list = None
    repl.choose_selected.clear()


def scan_choose_list(repl: "MergeRepl") -> bool:
    """扫描候选；成功则写入 repl.choose_list 并返回 True。"""
    if not os.path.isdir(repl.current_path):
        print(f"❌ 当前路径无效: {repl.current_path}")
        return False
    file_types, exc_skip_dirs, exc_file_rules = filter_settings_from_config(
        repl.config
    )
    scope = scope_settings_from_config(repl.config)
    paths, scan_error = collect_candidate_paths(
        repl.current_path,
        file_types,
        exc_skip_dirs,
        exc_file_rules,
        scope.max_depth,
        scope.exclude,
        scope.include,
    )
    if scan_error:
        print(f"❌ 扫描失败: {scan_error}")
        return False
    assert paths is not None
    limit = repl.config.c_limit
    if len(paths) > limit:
        print(
            f"❌ 候选文件 {len(paths)} 个，超过 c limit ({limit})。"
            f"请缩小目录、调整 mod/exc/this，或执行: c limit {len(paths)}"
        )
        return False
    repl.choose_list = paths
    return True


def print_choose_file_list(repl: "MergeRepl") -> None:
    assert repl.choose_list is not None
    print(f"\n[c] 可选文件共 {len(repl.choose_list)} 个（mod+exc 后）:\n")
    for idx, rel in enumerate(repl.choose_list, 1):
        mark = "*" if idx in repl.choose_selected else " "
        print(f"  {idx:4d}{mark}  {rel}")
    print("")


def print_choose_selected_line(repl: "MergeRepl") -> None:
    if not repl.choose_mode:
        return
    if not repl.choose_selected:
        print("📌 已选: (无)")
        return
    if repl.choose_list is None:
        print("📌 已选: (尚未列出候选，输入 c ll 列出)")
        return
    parts: list[str] = []
    for idx in sorted(repl.choose_selected):
        if 1 <= idx <= len(repl.choose_list):
            parts.append(f"{idx} {repl.choose_list[idx - 1]}")
    print("📌 已选: " + ", ".join(parts))


def _parse_indices(repl: "MergeRepl", tokens: list[str]) -> tuple[list[int], list[str]]:
    valid: list[int] = []
    invalid: list[str] = []
    if repl.choose_list is None:
        print("❌ 请先输入 c ll 列出候选文件。")
        return [], tokens
    max_n = len(repl.choose_list)
    for tok in tokens:
        try:
            n = int(tok)
        except ValueError:
            invalid.append(tok)
            continue
        if n < 1 or n > max_n:
            invalid.append(tok)
            continue
        valid.append(n)
    return valid, invalid


def _report_invalid(invalid: list[str], verb: str) -> None:
    if invalid:
        print(f"⚠️ 已忽略无效编号: {', '.join(invalid)} ({verb})")


def handle_choose(repl: "MergeRepl", payload: tuple[str, object]) -> None:
    cmd, data = payload

    if cmd == "toggle":
        if repl.choose_mode:
            repl.choose_mode = False
            invalidate_choose_state(repl)
            print("✅ 已关闭 c 模式，已清空选择。")
        else:
            repl.choose_mode = True
            repl.choose_selected.clear()
            repl.choose_list = None
            print("✅ 已开启 c 模式（点名合并）。输入 c ll 列出候选，再 c 关闭。")
        return

    if cmd == "list":
        if not repl.choose_mode:
            print("❌ 请先输入 c 开启 c 模式。")
            return
        if not scan_choose_list(repl):
            return
        print_choose_file_list(repl)
        return

    if cmd in ("limit_show", "limit_set"):
        if not repl.choose_mode:
            print("❌ c limit 仅在 c 模式下可用，请先输入 c 开启。")
            return
        if cmd == "limit_show":
            print(f"当前 c limit: {repl.config.c_limit}")
            return
        try:
            n = int(str(data))
        except (TypeError, ValueError):
            print("❌ c limit 需要正整数，例如: c limit 100")
            return
        if n < 1:
            print("❌ c limit 必须 ≥ 1")
            return
        repl.config.c_limit = n
        save_config(repl.config)
        print(f"✅ c limit 已设为 {n}")
        return

    if not repl.choose_mode:
        print("❌ 请先输入 c 开启 c 模式。")
        return

    if cmd == "deselect_usage":
        print("用法: c s <编号...>  或  c s all  取消已选")
        return

    if cmd == "select_all":
        if not scan_choose_list(repl):
            return
        repl.choose_selected = set(range(1, len(repl.choose_list) + 1))
        print(f"✅ 已全选 {len(repl.choose_selected)} 个文件。")
        return

    if cmd == "deselect_all":
        if repl.choose_list is None:
            if not scan_choose_list(repl):
                return
        repl.choose_selected.clear()
        print("✅ 已取消全部选择。")
        return

    if cmd == "select":
        valid, invalid = _parse_indices(repl, list(data))  # type: ignore[arg-type]
        for n in valid:
            repl.choose_selected.add(n)
        _report_invalid(invalid, "超出范围或非数字")
        if valid:
            print(f"✅ 已选 {len(repl.choose_selected)} 个文件。")
        return

    if cmd == "deselect":
        valid, invalid = _parse_indices(repl, list(data))  # type: ignore[arg-type]
        not_selected = [n for n in valid if n not in repl.choose_selected]
        for n in valid:
            repl.choose_selected.discard(n)
        _report_invalid(invalid + [str(x) for x in not_selected], "无效或未在已选列表中")
        if valid:
            print(f"✅ 当前已选 {len(repl.choose_selected)} 个文件。")
        return

    print(f"⚠️ 未处理的 c 子命令: {cmd}")
