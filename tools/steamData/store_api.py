"""
Steam Store 公开 JSON API（与网页解析互补）。

参考社区文档：https://wiki.teamfortress.com/wiki/User:GJohn/SteamWebAPI
及 store.steampowered.com 实际接口。单游戏抓取建议走 appdetails + appreviews 摘要。
"""

from __future__ import annotations

import logging
import re
from typing import Any

from config import STEAM_API_CC, STEAM_API_LANGUAGE, USE_STORE_API

logger = logging.getLogger(__name__)


def extract_app_id(url: str) -> int | None:
    m = re.search(r"/app/(\d+)", url, re.IGNORECASE)
    if not m:
        return None
    return int(m.group(1))


def _appdetails_url(app_id: int) -> str:
    return (
        "https://store.steampowered.com/api/appdetails"
        f"?appids={app_id}&l={STEAM_API_LANGUAGE}&cc={STEAM_API_CC}"
    )


def _appreviews_summary_url(app_id: int) -> str:
    return (
        "https://store.steampowered.com/appreviews/"
        f"{app_id}?json=1&language=all&purchase_type=all&filter=summary"
    )


def fetch_app_details_data(app_id: int) -> dict[str, Any] | None:
    from utils import send_request

    try:
        r = send_request(_appdetails_url(app_id))
        payload = r.json()
        entry = payload.get(str(app_id))
        if not entry or not entry.get("success"):
            logger.warning("appdetails: success=false 或无数据（可能锁区/下架/需年龄验证）")
            return None
        data = entry.get("data")
        if not isinstance(data, dict):
            return None
        return data
    except Exception as e:
        logger.warning(f"appdetails 请求解析失败: {e}")
        return None


def fetch_review_summary_text(app_id: int) -> str | None:
    from utils import send_request

    try:
        r = send_request(_appreviews_summary_url(app_id))
        j = r.json()
        qs = j.get("query_summary") or {}
        desc = qs.get("review_score_desc")
        if desc:
            return str(desc).strip()
        tp = int(qs.get("total_positive") or 0)
        tr = int(qs.get("total_reviews") or 0)
        if tr > 0:
            pct = round(100 * tp / tr)
            return f"{pct}%"
    except Exception as e:
        logger.debug(f"appreviews 摘要不可用: {e}")
    return None


def _price_from_details(d: dict[str, Any]) -> str:
    if d.get("is_free"):
        return "免费"
    po = d.get("price_overview")
    if isinstance(po, dict):
        fmt = po.get("final_formatted")
        if fmt:
            return str(fmt).strip()
        final = po.get("final")
        if final is not None:
            return str(final)
    return "未知"


def _tags_from_details(d: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    genres = d.get("genres") or []
    for g in genres[:2]:
        if isinstance(g, dict):
            t = (g.get("description") or "").strip()
            if t:
                tags.append(t)
    while len(tags) < 2:
        tags.append("")
    return tags


def _languages_from_details(d: dict[str, Any]) -> str:
    sl = d.get("supported_languages") or ""
    if isinstance(sl, str) and any(
        x in sl
        for x in (
            "简体中文",
            "繁体中文",
            "Traditional Chinese",
            "Simplified Chinese",
        )
    ):
        return "中文"
    return "无中文"


def build_game_data_from_store_api(url: str) -> dict[str, Any] | None:
    """用 Store API 构造与 scraper.parse_game_data 相同键结构的字典；失败返回 None。"""
    if not USE_STORE_API:
        return None
    app_id = extract_app_id(url)
    if not app_id:
        return None
    d = fetch_app_details_data(app_id)
    if not d:
        return None
    name = (d.get("name") or "").strip() or "未知"
    cover = d.get("header_image") or d.get("capsule_image")
    review = fetch_review_summary_text(app_id)
    if not review:
        review = "暂无评测"
    return {
        "name": name,
        "cover_image": cover,
        "price": _price_from_details(d),
        "review": review,
        "tags": _tags_from_details(d),
        "languages": _languages_from_details(d),
        "url": url,
    }
