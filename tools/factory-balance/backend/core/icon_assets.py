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
import struct
from pathlib import Path
from typing import Callable

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

_PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _read_png_size(filepath: Path) -> tuple[int, int] | None:
    """纯 Python 读取 PNG 文件宽高，不依赖 Pillow。"""
    try:
        with open(filepath, "rb") as f:
            if f.read(8) != _PNG_SIG:
                return None
            _ = struct.unpack(">I", f.read(4))[0]
            if f.read(4) != b"IHDR":
                return None
            w = struct.unpack(">I", f.read(4))[0]
            h = struct.unpack(">I", f.read(4))[0]
            return (w, h)
    except (OSError, struct.error):
        return None


def resolve_icon_file(icon_path: str, data_dir: Path) -> Path | None:
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


def icon_slug_from_path(icon_path: str) -> str:
    filename = icon_path.rsplit("/", 1)[-1]
    return filename.rsplit(".", 1)[0]


def _png_is_mipmap_strip(path: Path) -> bool:
    """PNG 图片是否为横向 mipmap 条带（width > height）。不依赖 Pillow。"""
    size = _read_png_size(path)
    return size is not None and size[0] > size[1]


def _crop_png_to_first_mipmap(path: Path) -> bool:
    """将 mipmap 条带文件原地裁剪到第一个 mipmap。需要 Pillow。"""
    if not _HAS_PIL:
        return False
    try:
        size = _read_png_size(path)
        if size is None or size[0] <= size[1]:
            return False
        img = Image.open(path)
        _, h = img.size
        cropped = img.crop((0, 0, h, h))
        cropped.save(path, format="PNG")
        return True
    except Exception:
        return False


def _crop_from_source(src: Path, dest: Path) -> bool:
    """从 Factorio 源文件复制并裁剪。需要 Pillow。"""
    if not _HAS_PIL:
        return False
    try:
        size = _read_png_size(src)
        if size is None or size[0] <= size[1]:
            shutil.copy2(src, dest)
            return False
        img = Image.open(src)
        _, h = img.size
        cropped = img.crop((0, 0, h, h))
        dest.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(dest, format="PNG")
        return True
    except Exception:
        return False


def extract_icon(
    icon_path: str,
    data_dir: Path | None,
    dest_dir: Path,
    *,
    warn_fn: Callable[[str], None] | None = None,
) -> tuple[str | None, str]:
    """提取单个图标。

    Returns:
        (icon_slug, status) — status 为 "new" / "ok" / "cropped" / "needs_pil" / "missing"
    """
    slug = icon_slug_from_path(icon_path)
    dest = dest_dir / f"{slug}.png"
    src = resolve_icon_file(icon_path, data_dir) if data_dir else None

    if src:
        if dest.is_file():
            if _png_is_mipmap_strip(dest):
                if _crop_from_source(src, dest):
                    return slug, "cropped"
                if warn_fn:
                    warn_fn(f"{slug}: 检测到 mipmap 条带但无法从源文件裁剪（Pillow 未安装？）")
                return slug, "needs_pil"
            return slug, "ok"
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            if _png_is_mipmap_strip(src):
                if _crop_from_source(src, dest):
                    return slug, "new"
                if warn_fn:
                    warn_fn(f"{slug}: 源文件是 mipmap 条带但无法裁剪（Pillow 未安装？）")
                return slug, "needs_pil"
            shutil.copy2(src, dest)
            return slug, "new"
    else:
        # Factorio 源不可用：尝试修复本地已有的 mipmap 条带
        if dest.is_file():
            if _png_is_mipmap_strip(dest):
                if _crop_png_to_first_mipmap(dest):
                    return slug, "cropped"
                if warn_fn:
                    warn_fn(f"{slug}: 本地图标是 mipmap 条带但无法裁剪（Pillow 未安装？）")
                return slug, "needs_pil"
            return slug, "ok"
        if warn_fn:
            warn_fn(f"{slug}: 找不到源文件且本地无缓存")
        return slug, "missing"


def extract_icon_from_proto(proto: dict, data_dir: Path | None, dest_dir: Path) -> str | None:
    icon_path = proto.get("icon")
    if icon_path:
        slug, _ = extract_icon(str(icon_path), data_dir, dest_dir)
        return slug
    icons = proto.get("icons")
    if isinstance(icons, list) and icons:
        first = icons[0]
        if isinstance(first, dict) and first.get("icon"):
            slug, _ = extract_icon(str(first["icon"]), data_dir, dest_dir)
            return slug
    return None


def resolve_data_dir_from_exe(exe_path: Path | None) -> Path | None:
    if not exe_path or not exe_path.is_file():
        return None
    install_dir = exe_path.parent.parent.parent
    data_dir = install_dir / "data"
    return data_dir if data_dir.is_dir() else None


def ensure_icons_extracted_from_db(icons_dir: Path) -> dict[str, int]:
    """扫描数据库中所有 icon 路径，补充/修复图标文件。

    即使 Factorio 可执行文件不可用，也会尝试修复本地已有的 mipmap 条带。

    Returns:
        {"new": n, "ok": n, "cropped": n, "needs_pil": n, "missing": n}
    """
    from db.connection import get_connection
    from .factorio_paths import load_paths

    data_dir = resolve_data_dir_from_exe(load_paths().executable)
    stats: dict[str, int] = {"new": 0, "ok": 0, "cropped": 0, "needs_pil": 0, "missing": 0}

    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT DISTINCT icon FROM snap_resource WHERE icon IS NOT NULL AND icon != ''"
        ).fetchall()
    finally:
        conn.close()

    warnings: list[str] = []

    def _warn(msg: str) -> None:
        warnings.append(msg)

    for row in rows:
        icon_path = str(row["icon"])
        slug, status = extract_icon(icon_path, data_dir, icons_dir, warn_fn=_warn)
        if slug:
            stats[status] = stats.get(status, 0) + 1

    for w in warnings[:3]:
        print(f"  [icon] {w}")
    if len(warnings) > 3:
        print(f"  [icon] ... 还有 {len(warnings) - 3} 个同类警告")

    return stats


def fix_existing_icons(icons_dir: Path) -> dict[str, int]:
    """不访问数据库，直接扫描本地 icons 目录并修复所有 mipmap 条带。"""
    stats = {"cropped": 0, "needs_pil": 0, "ok": 0}
    if not icons_dir.is_dir():
        return stats
    for f in icons_dir.glob("*.png"):
        if _png_is_mipmap_strip(f):
            if _crop_png_to_first_mipmap(f):
                stats["cropped"] += 1
            else:
                stats["needs_pil"] += 1
        else:
            stats["ok"] += 1
    return stats
