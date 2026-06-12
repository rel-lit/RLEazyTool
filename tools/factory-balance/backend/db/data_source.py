"""当前 catalog scope 对应的数据源 D 与分析上下文。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisContext:
    data_source: set[str]
    closure_expandable: set[str]
    pure_supply: set[str]
    scope_kind: str


def get_data_source_context(*, catalog_mode: str = "progress") -> AnalysisContext:
    """返回分析上下文。

    D = catalog.all_items（统一物品表）
    closure_expandable = 当前 gate 内可用 primary 配方制造的物品
    pure_supply = 基础可抽取物且当前无 primary 产法（默认外部供给）
    """
    from core.game_session import SESSION
    from db.catalog_builder import compute_scope_resource_names

    scope_kind = "environment" if catalog_mode == "full" else "save"
    catalog = SESSION.get_item_catalog(scope_kind)

    data_source = {i.name for i in catalog.all_items}
    closure_expandable: set[str] = set()
    pure_supply: set[str] = set()

    if SESSION.env_key:
        scope_key = SESSION.env_key if scope_kind == "environment" else (SESSION.active_save_key or "")
        if scope_key:
            ds, expandable, pure = compute_scope_resource_names(
                scope_kind=scope_kind,
                scope_key=scope_key,
                env_key=SESSION.env_key,
            )
            if ds:
                data_source = ds
            closure_expandable = expandable
            pure_supply = pure

    if not closure_expandable:
        closure_expandable = {i.name for i in catalog.manufacture_items} & data_source
    if not data_source:
        data_source = {i.name for i in catalog.manufacture_items} | {i.name for i in catalog.supply_items}

    return AnalysisContext(
        data_source=data_source,
        closure_expandable=closure_expandable,
        pure_supply=pure_supply,
        scope_kind=scope_kind,
    )


# 兼容旧调用名
def get_data_source_context_legacy(catalog_mode: str = "progress") -> tuple[set[str], set[str], str]:
    ctx = get_data_source_context(catalog_mode=catalog_mode)
    return ctx.data_source, ctx.closure_expandable, ctx.scope_kind
