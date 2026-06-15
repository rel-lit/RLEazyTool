"""本地图标存储管理。

职责单一：管理 `data/icons/` 目录，提供文件路径、尺寸检查、统计等运行时能力。
不涉及 Factorio 安装目录，也不做图像处理（那是 scripts/prepare_icons.py 的构建期职责）。
"""

from __future__ import annotations

import struct
from pathlib import Path

ICONS_DIR = Path(__file__).resolve().parent.parent / "data" / "icons"
_PNG_SIG = b"\x89PNG\r\n\x1a\n"


def icon_slug_from_path(icon_path: str) -> str:
    """__base__/graphics/icons/iron-plate.png → iron-plate"""
    filename = icon_path.rsplit("/", 1)[-1]
    return filename.rsplit(".", 1)[0]


def read_png_size(path: Path) -> tuple[int, int] | None:
    """不依赖 Pillow，直接读 PNG IHDR 获取宽高。"""
    try:
        with open(path, "rb") as f:
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


def png_is_mipmap_strip(path: Path) -> bool:
    """PNG 图片是否为横向 mipmap 条带（width > height）。"""
    size = read_png_size(path)
    return size is not None and size[0] > size[1]


def ensure_icons_dir() -> Path:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    return ICONS_DIR


def get_icon_file(slug: str) -> Path:
    return ICONS_DIR / f"{slug}.png"


def icon_exists(slug: str) -> bool:
    return get_icon_file(slug).is_file()


def list_icons() -> list[Path]:
    if not ICONS_DIR.is_dir():
        return []
    return sorted(ICONS_DIR.glob("*.png"))


def count_icons() -> int:
    return len(list_icons())


def count_mipmap_strips() -> int:
    return sum(1 for f in list_icons() if png_is_mipmap_strip(f))
