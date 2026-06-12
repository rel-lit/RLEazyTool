"""factory-balance 子工具专用 .venv（仅安装在本目录，不使用全局 Python）。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_TOOL_DIR = Path(__file__).resolve().parent
VENV_DIR = _TOOL_DIR / ".venv"
REQUIREMENTS = _TOOL_DIR / "requirements.txt"


def venv_python() -> Path | None:
    if sys.platform == "win32":
        exe = VENV_DIR / "Scripts" / "python.exe"
    else:
        exe = VENV_DIR / "bin" / "python"
    return exe if exe.is_file() else None


def ensure_venv(*, quiet: bool = True) -> tuple[bool, str]:
    """创建子工具 .venv 并安装 requirements.txt。"""
    if venv_python() is None:
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(VENV_DIR)],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as e:
            detail = ""
            if isinstance(e, subprocess.CalledProcessError) and e.stderr:
                detail = e.stderr.strip()[:200]
            return False, f"无法创建 {VENV_DIR}。{detail}".strip()

    vpy = venv_python()
    if vpy is None:
        return False, f"未找到子工具虚拟环境: {VENV_DIR}"

    pip_args = [str(vpy), "-m", "pip", "install"]
    if quiet:
        pip_args.append("-q")
    pip_args.extend(["-r", str(REQUIREMENTS)])
    try:
        subprocess.run(pip_args, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as e:
        detail = ""
        if isinstance(e, subprocess.CalledProcessError) and e.stderr:
            detail = e.stderr.strip()[:200]
        return False, f"在子工具 .venv 中安装依赖失败。{detail}".strip()

    return True, str(vpy)


if __name__ == "__main__":
    if sys.platform == "win32":
        for _stream in (sys.stdout, sys.stderr):
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError, ValueError):
                pass
    ok, msg = ensure_venv(quiet="--verbose" not in sys.argv)
    if ok:
        print(f"[factory-balance] 虚拟环境就绪: {msg}")
        sys.exit(0)
    print(f"[factory-balance] 错误: {msg}", file=sys.stderr)
    sys.exit(1)
