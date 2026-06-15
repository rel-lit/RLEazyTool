"""Factorio 图标路径解析。

职责单一：把原型里的 `__base__/graphics/icons/foo.png` 解析为实际文件系统路径。
"""

from __future__ import annotations

from pathlib import Path

_MOD_PREFIX_MAP = {
    "__base__": "base",
    "__core__": "core",
    "__space-age__": "space-age",
    "__quality__": "quality",
}


def resolve_factorio_icon_path(icon_path: str, data_dir: Path) -> Path | None:
    """将 Factorio 模组路径解析为实际文件路径。

    __base__/graphics/icons/iron-plate.png
        → <data_dir>/base/graphics/icons/iron-plate.png
    """
    if not icon_path or not data_dir.is_dir():
        return None
    for prefix, mod_dir in _MOD_PREFIX_MAP.items():
        if icon_path.startswith(prefix + "/"):
            relative = icon_path[len(prefix) + 1 :]
            resolved = data_dir / mod_dir / relative
            if resolved.is_file():
                return resolved
            break
    return None


def resolve_factorio_data_dir(exe_path: Path | None) -> Path | None:
    """从 Factorio 可执行文件路径推导 data/ 目录。

    Factorio 目录结构：<install>/bin/x64/Factorio.exe
    data 目录：<install>/data/
    """
    if not exe_path or not exe_path.is_file():
        return None
    install_dir = exe_path.parent.parent.parent
    data_dir = install_dir / "data"
    return data_dir if data_dir.is_dir() else None
