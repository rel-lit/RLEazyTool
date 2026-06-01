"""this 模式：目录范围配置。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from scope_rules import (
    folder_marker,
    format_saved_scope_hint,
    is_top_level_folder_path,
    iter_all_folder_nodes,
    list_folder_nodes_at_layer,
    min_file_depth_under_prefix,
    norm_rel_path,
)
from storage import save_config

if TYPE_CHECKING:
    from repl import MergeRepl


def invalidate_scope_on_path_change(config) -> None:
    config.merge_scope_exclude = []
    config.merge_scope_include = []


def _apply_merge_max_depth(repl: "MergeRepl", depth: int | None) -> None:
    """仅保存深度；是否作用于合并由 this 开关（scope_enabled）决定。"""
    repl.config.merge_max_depth = depth
    repl.config.merge_layer_only = depth == 0  # 内存同步，便于旧逻辑；不再写入 JSON
    if depth == 0:
        repl.config.merge_scope_exclude = []
        repl.config.merge_scope_include = []
    repl._depth_include_warned = False


def _bind_source(repl: "MergeRepl") -> str:
    return repl.current_path


def print_scope_list_layer(repl: "MergeRepl", layer: int) -> None:
    src = _bind_source(repl)
    folders = list_folder_nodes_at_layer(src, layer)
    max_d = repl.config.merge_max_depth
    depth_hint = (
        "不限深度"
        if max_d is None
        else ("仅本层" if max_d == 0 else f"最大深度 {max_d}")
    )
    print(
        f"\n[this ll {layer}] 第 {layer} 层文件夹（当前合并: {depth_hint}）\n"
        "[*] 顶层默认纳入且不可排除\n"
    )
    if not folders:
        print("  (无)")
    for name in folders:
        mark = folder_marker(
            name,
            tuple(repl.config.merge_scope_exclude),
            tuple(repl.config.merge_scope_include),
            is_top_level=(layer == 0),
        )
        print(f"  {mark}  {name}")
    _print_scope_rules_hint(repl)
    print()


def print_scope_list_all(repl: "MergeRepl") -> None:
    src = _bind_source(repl)
    nodes = iter_all_folder_nodes(src)
    max_d = repl.config.merge_max_depth
    depth_hint = (
        "不限深度"
        if max_d is None
        else ("仅本层" if max_d == 0 else f"最大深度 {max_d}")
    )
    print(f"\n[this ll all] 目录树可配置节点（当前合并: {depth_hint}）:\n")
    if not nodes:
        print("  (无子目录)")
    for name in nodes:
        mark = folder_marker(
            name,
            tuple(repl.config.merge_scope_exclude),
            tuple(repl.config.merge_scope_include),
            is_top_level=is_top_level_folder_path(name),
        )
        print(f"  {mark}  {name}")
    _print_scope_rules_hint(repl)
    print()


def _print_scope_rules_hint(repl: "MergeRepl") -> None:
    exc = repl.config.merge_scope_exclude
    inc = repl.config.merge_scope_include
    if exc:
        print("  排除: " + ", ".join(exc))
    if inc:
        print("  细则包含: " + ", ".join(inc))


def _reject_top_level_exclude(repl: "MergeRepl", path: str) -> bool:
    if is_top_level_folder_path(path):
        print(
            f"❌ 不能排除顶层文件夹「{path}」。若不要其中文件，请用 c 模式按文件排除。"
        )
        return True
    return False


def _warn_include_deeper_than_max(repl: "MergeRepl", path: str) -> None:
    max_d = repl.config.merge_max_depth
    if max_d is None or getattr(repl, "_depth_include_warned", False):
        return
    if min_file_depth_under_prefix(path) > max_d:
        print(
            f"ℹ️ 「{path}」下文件深度超过当前最大深度 {max_d}，"
            "细则包含不会生效；可先 this max 或增大 this N。"
        )
        repl._depth_include_warned = True


def handle_this(repl: "MergeRepl", payload: tuple[str, object]) -> None:
    cmd, data = payload

    if cmd == "toggle":
        if repl.this_mode:
            repl.this_mode = False
            repl.config.scope_enabled = False
            save_config(repl.config)
            saved = format_saved_scope_hint(
                repl.config.merge_max_depth,
                tuple(repl.config.merge_scope_exclude),
                tuple(repl.config.merge_scope_include),
            )
            if saved != "无":
                print(
                    "✅ 已退出 this 配置模式；合并不再应用目录范围限制。"
                    f" 已保存: {saved}（再次输入 this 可重新启用）"
                )
            else:
                print("✅ 已退出 this 配置模式；合并不限制目录范围。")
        else:
            repl.this_mode = True
            repl.config.scope_enabled = True
            save_config(repl.config)
            print(
                "✅ 已进入 this 范围配置模式（合并将应用已保存的范围设置）。"
                " this 0/N/max | this ll / this ll N / this ll all | this a / this s"
            )
        return

    if cmd == "set_depth":
        depth = data  # int | None
        _apply_merge_max_depth(repl, depth)
        save_config(repl.config)
        repl._invalidate_choose("已修改合并深度")
        if repl.this_mode:
            apply_hint = "合并将按此深度生效。"
        else:
            apply_hint = "已保存；合并不受限（输入 this 进入配置模式后生效）。"
        if depth is None:
            print(f"✅ 已保存: 不限深度。{apply_hint}")
        elif depth == 0:
            print(f"✅ 已保存: 仅本层文件（深度 0）。{apply_hint}")
        else:
            print(f"✅ 已保存: 最大深度 {depth}。{apply_hint}")
        return

    if cmd == "list":
        layer = int(data) if data is not None else 0
        if not repl.this_mode:
            print("❌ 请先输入 this 进入范围配置模式。")
            return
        print_scope_list_layer(repl, layer)
        return

    if cmd == "list_all":
        if not repl.this_mode:
            print("❌ 请先输入 this 进入范围配置模式。")
            return
        print_scope_list_all(repl)
        return

    if cmd in ("exclude", "exclude_usage", "include"):
        if cmd == "exclude_usage":
            print("用法: this s <相对路径...>  排除子路径（不可排除顶层文件夹）")
            return
        if not repl.this_mode:
            print("❌ 请先输入 this 进入范围配置模式。")
            return
        paths = [norm_rel_path(str(p)) for p in (data or [])]  # type: ignore[arg-type]
        if not paths:
            print("❌ 请提供路径。")
            return
        if repl.config.merge_max_depth == 0:
            _apply_merge_max_depth(repl, None)
            print("ℹ️ 已自动切换为不限深度，以便配置子路径细则。")
        if cmd == "exclude":
            for p in paths:
                if _reject_top_level_exclude(repl, p):
                    continue
                if p not in repl.config.merge_scope_exclude:
                    repl.config.merge_scope_exclude.append(p)
                    print(f"✅ 已排除: {p}")
                repl.config.merge_scope_include = [
                    x
                    for x in repl.config.merge_scope_include
                    if not _path_prefix_match(x, p)
                ]
            save_config(repl.config)
            repl._invalidate_choose("已修改范围")
            return
        for p in paths:
            _warn_include_deeper_than_max(repl, p)
            if p not in repl.config.merge_scope_include:
                repl.config.merge_scope_include.append(p)
                print(f"✅ 已添加细则包含: {p}")
        save_config(repl.config)
        repl._invalidate_choose("已修改范围")
        return

    print(f"⚠️ 未处理的 this 子命令: {cmd}")


def _path_prefix_match(a: str, b: str) -> bool:
    a, b = norm_rel_path(a), norm_rel_path(b)
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")
