"""Factorio 物品图标解析与提取。

职责：
  1. 将 Factorio 原型中的图标路径（__base__/graphics/icons/foo.png）
     解析为实际文件系统路径
  2. 将 PNG 图标从 Factorio 安装目录复制到工具的数据目录
  3. 检测并裁剪 mipmap 条带，仅保留第一级（真图标）
  4. 支持 icon（单路径）和 icons（分层数组）两种原型格式

Factorio 2.0 图标格式：
  源 PNG 是横向 mipmap 条带，例如 icon_size=64 时文件为 120×64：
    mip0 (64×64) | mip1 (32×32) | mip2 (16×16) | mip3 (8×8)
  仅最左边的 icon_size×icon_size 区域是真正的图标。
"""

from __future__ import annotations

import shutil
from pathlib import Path

try:
    from PIL import Image

    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

_MOD_PREFIX_MAP = {
    "__base__": "base",
    "__core__": "core",
    "__space-age__": "space-age",
    "__quality__": "quality",
}


def resolve_icon_file(icon_path: str, data_dir: Path) -> Path | None:
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
    filename = icon_path.rsplit("/", 1)[-1]
    return filename.rsplit(".", 1)[0]


def _crop_first_mipmap(src: Path, dest: Path) -> bool:
    """如果图像是横向 mipmap 条带（width > height），裁剪到第一个 mipmap 大小并覆写。

    Returns:
        True 如果进行了裁剪（图像被修改），False 如果图像已经是方形的。
    """
    if not _HAS_PIL:
        return False
    try:
        img = Image.open(src)
        w, h = img.size
        if w <= h:
            return False
        cropped = img.crop((0, 0, h, h))
        dest.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(dest, format="PNG")
        return True
    except Exception:
        return False


def _is_mipmap_strip(path: Path) -> bool:
    if not _HAS_PIL or not path.is_file():
        return False
    try:
        img = Image.open(path)
        return img.size[0] > img.size[1]
    except Exception:
        return False


def extract_icon(icon_path: str, data_dir: Path, dest_dir: Path, *, force: bool = False) -> str | None:
    src = resolve_icon_file(icon_path, data_dir)
    if not src:
        return None
    slug = icon_slug_from_path(icon_path)
    dest = dest_dir / f"{slug}.png"

    if dest.is_file():
        if force or _is_mipmap_strip(dest):
            _crop_first_mipmap(src, dest)
        return slug

    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    _crop_first_mipmap(src, dest)
    return slug


def extract_icon_from_proto(proto: dict, data_dir: Path, dest_dir: Path) -> str | None:
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
    result: dict[str, str] = {}
    for name, icon_path in resources:
        if not icon_path:
            continue
        slug = extract_icon(icon_path, data_dir, dest_dir)
        if slug:
            result[name] = slug
    return result


def resolve_data_dir_from_exe(exe_path: Path | None) -> Path | None:
    if not exe_path or not exe_path.is_file():
        return None
    install_dir = exe_path.parent.parent.parent
    data_dir = install_dir / "data"
    return data_dir if data_dir.is_dir() else None


def ensure_icons_extracted_from_db(icons_dir: Path, *, force: bool = False) -> int:
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
        slug = extract_icon(icon_path, data_dir, icons_dir, force=force)
        if slug:
            count += 1
    return count
