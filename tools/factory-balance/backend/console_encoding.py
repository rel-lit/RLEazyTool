"""Windows 控制台 UTF-8 输出（供入口脚本 import）。"""

from __future__ import annotations

import sys


def configure_console_utf8() -> None:
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass
