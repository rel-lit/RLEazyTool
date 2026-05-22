"""ana：详细语法分析开关（默认仅粗略统计）。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from analysis.tree_loader import tree_sitter_available
from storage import save_config
from venv_bootstrap import ensure_merge_deps

if TYPE_CHECKING:
    from repl import MergeRepl


def handle_ana(repl: "MergeRepl", payload: tuple[str, object]) -> None:
    cmd, _data = payload
    if cmd == "show":
        on = repl.config.detail_analysis
        print(f"  详细语法分析: {'开' if on else '关'}（默认关，仅粗略行数/体量统计）")
        if on and not tree_sitter_available():
            print("  tree-sitter: 未就绪（合并时将尝试在 .venv 自动安装）")
        elif on:
            print("  tree-sitter: 已就绪")
        return

    if cmd == "toggle":
        if repl.config.detail_analysis:
            repl.config.detail_analysis = False
            save_config(repl.config)
            print("✅ 已关闭详细语法分析（合并输出仅含粗略统计）。")
            return
        ok, note = ensure_merge_deps(quiet=True)
        repl.config.detail_analysis = True
        save_config(repl.config)
        if note:
            print(f"ℹ️ {note}")
        if ok:
            print(
                "✅ 已开启详细语法分析（tree-sitter，合并头含符号级统计；"
                "解析失败的文件仍会合并，仅跳过该文件分析）。"
            )
        else:
            print(
                "✅ 已开启详细语法分析；tree-sitter 未就绪，合并时将再次尝试在 .venv 安装。"
            )
        return

    print(f"⚠️ 未处理的 ana 子命令: {cmd}")
