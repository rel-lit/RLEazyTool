"""构建期脚本：从 Factorio 安装目录提取并裁剪物品图标。

用法：
    python scripts/prepare_icons.py [--factorio-exe PATH]

说明：
    这是数据准备脚本，不是运行时服务。它读取 SQLite 中 snap_resource.icon
    记录，把 Factorio 源文件复制到 backend/data/icons/，并把横向 mipmap
    条带裁剪为第一个 mipmap 的方形 PNG。

    服务端运行时不需要运行此脚本；data/icons/ 目录会被提交/分发。只有
    在 Factorio 数据更新、新增物品或发现图标损坏时才需要重新执行。
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# 让脚本能找到 backend 下的模块
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

try:
    from PIL import Image
except ImportError as e:
    print("错误：需要 Pillow 才能裁剪图标。请安装：pip install Pillow")
    raise SystemExit(1) from e

from db.connection import get_connection
from core.icon_paths import resolve_factorio_data_dir, resolve_factorio_icon_path
from core.icon_store import (
    ICONS_DIR,
    icon_slug_from_path,
    png_is_mipmap_strip,
    read_png_size,
)


def _crop_first_mipmap(src: Path, dest: Path) -> bool:
    """从源文件读取，裁剪第一个 mipmap，写入目标文件。"""
    try:
        size = read_png_size(src)
        if size is None:
            return False
        w, h = size
        img = Image.open(src)
        if w <= h:
            # 已经是方图，直接复制
            shutil.copy2(src, dest)
            return False
        cropped = img.crop((0, 0, h, h))
        dest.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(dest, format="PNG")
        return True
    except Exception as exc:
        print(f"  裁剪失败 {src.name}: {exc}")
        return False


def prepare_icons(data_dir: Path) -> dict[str, int]:
    """根据数据库里的 icon 记录准备图标文件。"""
    stats = {"new": 0, "cropped": 0, "ok": 0, "missing": 0}

    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT DISTINCT icon FROM snap_resource WHERE icon IS NOT NULL AND icon != ''"
        ).fetchall()
    finally:
        conn.close()

    for row in rows:
        icon_path = str(row["icon"])
        slug = icon_slug_from_path(icon_path)
        dest = ICONS_DIR / f"{slug}.png"
        src = resolve_factorio_icon_path(icon_path, data_dir)

        if src is None:
            print(f"  源文件缺失: {icon_path}")
            stats["missing"] += 1
            continue

        if dest.is_file():
            if png_is_mipmap_strip(dest):
                if _crop_first_mipmap(src, dest):
                    stats["cropped"] += 1
                else:
                    stats["ok"] += 1
            else:
                stats["ok"] += 1
        else:
            if _crop_first_mipmap(src, dest):
                stats["new"] += 1
            else:
                stats["new"] += 1

    return stats


def _detect_factorio_data_dir() -> Path | None:
    from core.factorio_paths import load_paths

    return resolve_factorio_data_dir(load_paths().executable)


def main() -> int:
    parser = argparse.ArgumentParser(description="从 Factorio 提取并裁剪物品图标")
    parser.add_argument(
        "--factorio-exe",
        type=Path,
        help="Factorio 可执行文件路径（可选，默认自动检测）",
    )
    args = parser.parse_args()

    if args.factorio_exe:
        data_dir = resolve_factorio_data_dir(args.factorio_exe)
    else:
        data_dir = _detect_factorio_data_dir()

    if not data_dir:
        print("错误：未找到 Factorio data/ 目录。请指定 --factorio-exe 或设置 FACTORIO_EXE 环境变量。")
        return 1

    print(f"使用 Factorio 数据目录: {data_dir}")
    print(f"输出目录: {ICONS_DIR}")

    stats = prepare_icons(data_dir)

    parts = []
    if stats["new"]:
        parts.append(f"新增 {stats['new']} 个")
    if stats["cropped"]:
        parts.append(f"裁剪 {stats['cropped']} 个")
    if stats["ok"]:
        parts.append(f"已就绪 {stats['ok']} 个")
    if stats["missing"]:
        parts.append(f"缺失 {stats['missing']} 个")

    print(f"完成。{', '.join(parts) if parts else '无变化'}。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
