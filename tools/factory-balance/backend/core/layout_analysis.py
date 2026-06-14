"""布局 analysis 元数据：与前端 domains/layout-analysis 字段对齐。"""

from __future__ import annotations

from typing import Any


def build_layout_analysis_meta(
    *,
    declared_outputs: list[str],
    terminals: list[str],
    analysis_items: set[str] | list[str],
    recipe_assignments: dict[str, str],
    pseudo_external: set[str] | list[str],
    impossible: bool,
    max_layer: int | None = None,
) -> dict[str, Any]:
    """产出 effective_terminals / demoted_outputs 等规范字段。"""
    effective_terminals = list(terminals)
    effective_set = set(effective_terminals)
    demoted_outputs = [d for d in declared_outputs if d not in effective_set]
    pseudo = sorted(pseudo_external)
    items = sorted(analysis_items)

    meta: dict[str, Any] = {
        "declared_outputs": declared_outputs,
        "effective_terminals": effective_terminals,
        "terminals": effective_terminals,
        "demoted_outputs": demoted_outputs,
        "analysis_items": items,
        "recipe_assignments": recipe_assignments,
        "pseudo_pure_sources": pseudo,
        "pseudo_external": pseudo,
        "true_pure_sources": [],
        "impossible": impossible,
    }
    if max_layer is not None:
        meta["max_layer"] = max_layer
    return meta
