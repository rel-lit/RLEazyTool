"""入口：保持 `py main.py` / merge.bat 可用。"""

import sys

from venv_bootstrap import ensure_pathspec


def _bootstrap() -> None:
    """在加载 repl（会 import parsy）之前安装并注入 core 依赖。"""
    ok, note = ensure_pathspec(quiet=True)
    if not ok:
        print(f"⚠️ {note}")
        print("请手动执行: pip install -r tools/merge/requirements-core.txt")
        sys.exit(1)
    if note:
        print(note)


if __name__ == "__main__":
    _bootstrap()
    from repl import main

    main()
