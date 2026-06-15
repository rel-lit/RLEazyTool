"""Factorio 物品图标解析与提取。

职责：
  1. 将 Factorio 原型中的图标路径（__base__/graphics/icons/foo.png）
     解析为实际文件系统路径
  2. 将 PNG 图标从 Factorio 安装目录复制到工具的数据目录
  3. 支持 icon（单路径）和 icons（分层数组）两种原型格式
"""

from __future__ import annotations

import shutil
from pathlib import Path

_MOD_PREFIX_MAP = {
    "__base__": "base",
    "__core__": "core",
    "__space-age__": "space-age",
    "__quality__": "quality",
}


def resolve_icon_file(icon_path: str, data_dir: Path) -> Path | None:
    """将 Factorio 模组路径解析为实际文件路径。

    __base__/graphics/icons/iron-plate.png
        → <data_dir>/base/graphics/icons/iron-plate.png
    """
    if not icon_path or not data_dir.is_dir():
        return None
    for prefix, mod_dir in _MOD_PREFIX_MAP.items():
        if icon_path.startswith(prefix + "/"):
            relative = icon_path[len(prefix) + 1:]
            resolved = data_dir / mod_dir / relative
            if resolved.is_file():
                return resolved
            break
    return None


def icon_slug_from_path(icon_path: str) -> str:
    """从 Factorio 图标路径提取文件名（不含扩展名）作为 slug。

    __base__/graphics/icons/iron-plate.png → iron-plate
    """
    filename = icon_path.rsplit("/", 1)[-1]
    slug = filename.rsplit(".", 1)[0]
    return slug


def extract_icon(icon_path: str, data_dir: Path, dest_dir: Path) -> str | None:
    """将单个图标从 Factorio 数据目录提取到目标目录。

    Returns:
        成功时返回 icon_slug，失败或源文件不存在时返回 None
    """
    src = resolve_icon_file(icon_path, data_dir)
    if not src:
        return None
    slug = icon_slug_from_path(icon_path)
    dest = dest_dir / f"{slug}.png"
    if not dest.is_file():
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    return slug


def extract_icon_from_proto(proto: dict, data_dir: Path, dest_dir: Path) -> str | None:
    """从原型字典中提取图标路径并复制。

    支持两种格式：
      - icon: "__base__/graphics/icons/foo.png"        (单路径)
      - icons: [{icon: "path/to/layer1.png", ...}, ...] (分层数组，取第一层)
    """
    icon_path = proto.get("icon")
    if icon_path:
        return extract_icon(str(icon_path), data_dir, dest_dir)

    icons = proto.get("icons")
    if isinstance(icons, list) and icons:
        first = icons[0]
        if isinstance(first, dict) and first.get("icon"):
            return extract_icon(str(first["icon"]), data_dir, dest_dir)

    return None


def batch_extract_icons(
    resources: list[tuple[str, str | None]],
    data_dir: Path,
    dest_dir: Path,
) -> dict[str, str]:
    """批量提取图标。

    Args:
        resources: [(resource_name, icon_path), ...] 的列表
        data_dir: Factorio 安装目录下的 data/ 目录
        dest_dir: 图标输出目录

    Returns:
        {resource_name: icon_slug} 映射
    """
    result: dict[str, str] = {}
    for name, icon_path in resources:
        if not icon_path:
            continue
        slug = extract_icon(icon_path, data_dir, dest_dir)
        if slug:
            result[name] = slug
    return result


def resolve_data_dir_from_exe(exe_path: Path | None) -> Path | None:
    """从 Factorio 可执行文件路径推导 data/ 目录。

    Factorio 目录结构：<install>/bin/x64/Factorio.exe
    data 目录：<install>/data/
    """
    if not exe_path or not exe_path.is_file():
        return None
    install_dir = exe_path.parent.parent.parent
    data_dir = install_dir / "data"
    return data_dir if data_dir.is_dir() else None


def ensure_icons_extracted_from_db(icons_dir: Path) -> int:
    """扫描数据库中所有 snap_resource.icon 路径，补充提取缺失的图标 PNG。

    仅在 Factorio 可执行文件可用时生效；若 Factorio 未安装则静默跳过。

    Returns:
        成功提取的图标数量。
    """
    from db.connection import get_connection
    from .factorio_paths import load_paths

    data_dir = resolve_data_dir_from_exe(load_paths().executable)
    if not data_dir:
        return 0

    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT DISTINCT icon FROM snap_resource WHERE icon IS NOT NULL AND icon != ''"
        ).fetchall()
    finally:
        conn.close()

    count = 0
    for row in rows:
        icon_path = str(row["icon"])
        slug = extract_icon(icon_path, data_dir, icons_dir)
        if slug:
            count += 1
    return count
