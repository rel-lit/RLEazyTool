"""Layer IR — snap_resource 语义 tag 分类。"""

from __future__ import annotations

import json
from typing import Any

from db.intrinsic.constants import (
    IR_CONTAINER_BARREL,
    IR_EXTRACTABLE,
    IR_FLUID,
    IR_INTERNAL,
    IR_ITEM,
)


def classify_resource(
    *,
    name: str,
    kind: str,
    visibility: str,
    item_subgroup: str | None,
    proto: dict[str, Any] | None = None,
    world_extractable: set[tuple[str, str]] | None = None,
) -> tuple[set[str], dict[str, str] | None, bool]:
    """返回 (tags, params_json_dict, is_raw)。"""
    tags: set[str] = set()
    params: dict[str, str] | None = None
    proto = proto or {}
    world_extractable = world_extractable or set()

    if visibility == "internal" or name.startswith("parameter-"):
        tags.add(IR_INTERNAL)
        return tags, None, False

    if kind == "fluid":
        tags.add(IR_FLUID)
    else:
        tags.add(IR_ITEM)

    if name.endswith("-barrel"):
        tags.add(IR_CONTAINER_BARREL)
        fluid = name[: -len("-barrel")]
        params = {"content_fluid": fluid}

    is_extractable = _is_extractable(
        name,
        kind,
        item_subgroup,
        proto,
        world_extractable=world_extractable,
    )
    if is_extractable:
        tags.add(IR_EXTRACTABLE)

    return tags, params, is_extractable


def _is_extractable(
    name: str,
    kind: str,
    item_subgroup: str | None,
    proto: dict[str, Any],
    *,
    world_extractable: set[tuple[str, str]],
) -> bool:
    if (kind, name) in world_extractable:
        return True
    if item_subgroup == "raw-resource":
        return True
    if proto.get("subgroup") == "raw-resource":
        return True
    if name.endswith("-ore") or name.endswith("-brine"):
        return True
    return False


def params_to_json(params: dict[str, str] | None) -> str | None:
    return json.dumps(params, ensure_ascii=False) if params else None
