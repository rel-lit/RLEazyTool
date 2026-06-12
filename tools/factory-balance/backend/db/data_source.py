"""当前 catalog scope 对应的数据源 D。"""

from __future__ import annotations


def get_data_source_context(*, catalog_mode: str = "progress") -> tuple[set[str], set[str], str]:
    """返回 (data_source D, craftable_in_d, scope_kind)。

    D 的定义：当前 scope 下 catalog 的 **统一物品表**（all_items）。
    manufacture / supply 两个 UI 列表只是 D 上的不同 tag 视图，不是三个独立集合。
    """
    from core.game_session import SESSION

    scope_kind = "environment" if catalog_mode == "full" else "save"
    catalog = SESSION.get_item_catalog(scope_kind)

    # D = 原始列表（= 产出视图 ∪ 供给视图，去重）
    data_source = {i.name for i in catalog.all_items}
    if not data_source:
        data_source = {i.name for i in catalog.manufacture_items} | {
            i.name for i in catalog.supply_items
        }

    # 可制造 = 产出视图（manufacture tag）
    craftable_in_d = {i.name for i in catalog.manufacture_items} & data_source

    return data_source, craftable_in_d, scope_kind
