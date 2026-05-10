"""
用户配置持久化（终端修改后写入 steamdata_config.json）。

与 merge 工具的 merge_config.json 类似：代码内为默认值，磁盘覆盖同名属性。
"""

from __future__ import annotations

import json
import os
from typing import Any

CONFIG_FILENAME = "steamdata_config.json"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, CONFIG_FILENAME)

# 允许写入 JSON 的键（勿加入 HEADERS 等复杂对象）
PERSIST_KEYS: frozenset[str] = frozenset(
    {
        "CONNECTION_STRATEGY",
        "PROXIES",
        "CONNECT_TIMEOUT",
        "READ_TIMEOUT",
        "VERIFY_SSL",
        "USE_STORE_API",
        "STEAM_API_LANGUAGE",
        "STEAM_API_CC",
        "MAX_RETRIES",
        "RETRY_DELAY",
        "REQUEST_TIMEOUT",
        "EXCEL_FILENAME",
        "STORE_COUNTRY_COOKIE",
        "DEFAULT_ROW_HEIGHT",
        "IMAGE_COLUMN_WIDTH",
    }
)


def _normalize_loaded(k: str, v: Any) -> Any:
    if k == "PROXIES":
        if v in (None, {}, ""):
            return None
        if isinstance(v, dict):
            return dict(v)
    if k == "STORE_COUNTRY_COOKIE" and v == "":
        return None
    if k == "VERIFY_SSL":
        return bool(v)
    if k == "USE_STORE_API":
        return bool(v)
    return v


def load_and_apply() -> None:
    """将 steamdata_config.json 合并进 config 模块（存在则加载）。"""
    if not os.path.isfile(CONFIG_PATH):
        return
    import config

    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(raw, dict):
        return
    for k, v in raw.items():
        if k not in PERSIST_KEYS:
            continue
        if hasattr(config, k):
            setattr(config, k, _normalize_loaded(k, v))


def collect_for_save() -> dict[str, Any]:
    import config

    data: dict[str, Any] = {}
    for k in sorted(PERSIST_KEYS):
        if not hasattr(config, k):
            continue
        v = getattr(config, k)
        if k == "PROXIES" and v is not None:
            data[k] = dict(v)
        elif v is None and k == "STORE_COUNTRY_COOKIE":
            data[k] = None
        else:
            data[k] = v
    return data


def save_to_disk() -> bool:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(collect_for_save(), f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def delete_user_file() -> bool:
    try:
        if os.path.isfile(CONFIG_PATH):
            os.remove(CONFIG_PATH)
        return True
    except OSError:
        return False
