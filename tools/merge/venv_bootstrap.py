"""项目 .venv 与 merge 可选依赖的自动准备（仅写入项目内 .venv）。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_MERGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _MERGE_DIR.parent.parent
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS = _MERGE_DIR / "requirements.txt"
REQUIREMENTS_CORE = _MERGE_DIR / "requirements-core.txt"
REQUIREMENTS_EXTRA = _MERGE_DIR / "requirements-extra.txt"


def project_venv_python() -> Path | None:
    if sys.platform == "win32":
        exe = VENV_DIR / "Scripts" / "python.exe"
    else:
        exe = VENV_DIR / "bin" / "python"
    return exe if exe.is_file() else None


def project_venv_site_packages() -> Path | None:
    if not VENV_DIR.is_dir():
        return None
    if sys.platform == "win32":
        candidate = VENV_DIR / "Lib" / "site-packages"
    else:
        lib = VENV_DIR / "lib"
        if not lib.is_dir():
            return None
        subs = sorted(lib.glob("python*"))
        candidate = subs[0] / "site-packages" if subs else None
    return candidate if candidate.is_dir() else None


def _inject_venv_site_packages() -> bool:
    site = project_venv_site_packages()
    if site is None:
        return False
    site_str = str(site)
    if site_str not in sys.path:
        sys.path.insert(0, site_str)
    return True


def _try_import_pathspec() -> bool:
    try:
        import pathspec  # noqa: F401

        return True
    except ImportError:
        return False


def _try_import_tree_sitter() -> bool:
    try:
        import tree_sitter  # noqa: F401

        return True
    except ImportError:
        return False


def _try_import_parsy() -> bool:
    try:
        import parsy  # noqa: F401

        return True
    except ImportError:
        return False


def ensure_project_venv() -> bool:
    if project_venv_python() is not None:
        return True
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return project_venv_python() is not None


def _pip_install_files(
    req_files: list[Path], *, quiet: bool
) -> tuple[bool, str]:
    if not ensure_project_venv():
        return False, "无法创建项目 .venv，请检查 Python 安装。"

    vpy = project_venv_python()
    if vpy is None:
        return False, "未找到项目 .venv 中的 Python。"

    pip_args = [str(vpy), "-m", "pip", "install"]
    if quiet:
        pip_args.append("-q")
    for rf in req_files:
        pip_args.extend(["-r", str(rf)])
    try:
        subprocess.run(
            pip_args,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as e:
        detail = ""
        if isinstance(e, subprocess.CalledProcessError) and e.stderr:
            detail = e.stderr.strip()[:200]
        return False, f"在 .venv 中安装依赖失败。{detail}".strip()

    _inject_venv_site_packages()
    return True, "已自动在项目 .venv 中安装 merge 可选依赖。"


def ensure_analysis_extra(*, quiet: bool = True) -> tuple[bool, str]:
    """仅安装扩展语言 grammar（requirements-extra.txt）。"""
    ok, note = _pip_install_files([REQUIREMENTS_EXTRA], quiet=quiet)
    if ok:
        from analysis.tree_loader import get_parser

        get_parser.cache_clear()  # type: ignore[attr-defined]
    return ok, note


def ensure_merge_deps(*, quiet: bool = True) -> tuple[bool, str]:
    """pathspec + parsy + tree-sitter 核心 + 扩展 grammar。"""
    if (
        _try_import_pathspec()
        and _try_import_tree_sitter()
        and _try_import_parsy()
    ):
        return True, ""
    ok, note = _pip_install_files(
        [REQUIREMENTS_CORE, REQUIREMENTS_EXTRA], quiet=quiet
    )
    if not ok:
        return False, note
    if _try_import_pathspec() and _try_import_tree_sitter() and _try_import_parsy():
        return True, note
    return False, note + " 部分依赖仍无法导入。" if note else "部分依赖仍无法导入。"


def ensure_pathspec(*, quiet: bool = True) -> tuple[bool, str]:
    """gitignore / 基础：仅安装 requirements-core（体积较小）。"""
    if _try_import_pathspec() and _try_import_parsy():
        return True, ""
    ok, note = _pip_install_files([REQUIREMENTS_CORE], quiet=quiet)
    if not ok:
        return False, note
    if _try_import_pathspec() and _try_import_parsy():
        return True, note
    if not _try_import_pathspec():
        return False, "pathspec 安装后仍无法导入。"
    return False, "parsy 安装后仍无法导入（REPL 指令解析需要）。"
