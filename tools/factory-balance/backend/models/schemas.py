"""Pydantic 模型：请求/响应与占位扩展字段。"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SupplyMode(str, Enum):
    RAW = "raw"
    DIRECT = "direct"


class PrimaryDirection(str, Enum):
    LEFT_TO_RIGHT = "left-to-right"
    TOP_TO_BOTTOM = "top-to-bottom"


class LayoutTarget(BaseModel):
    item: str
    rate_per_minute: float | None = None  # Phase 2 占位


class LayoutOptions(BaseModel):
    primary_direction: PrimaryDirection = PrimaryDirection.LEFT_TO_RIGHT
    allow_detour: bool = True
    buffer_recommendation: bool = True


class LayoutComputeRequest(BaseModel):
    targets: list[LayoutTarget]
    supply_mode: SupplyMode = SupplyMode.RAW
    supplied_items: list[str] = Field(default_factory=list)
    forbidden_items: list[str] = Field(default_factory=list)
    catalog_mode: str = Field(default="progress", description="progress | full，与 UI 列表 scope 一致")
    layout_options: LayoutOptions = Field(default_factory=LayoutOptions)


class Position(BaseModel):
    x: float
    y: float


class LayoutNode(BaseModel):
    id: str
    type: str  # supply | producer | sink | buffer_placeholder
    item: str
    label: str
    layer: int
    position: Position
    recipe: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class LayoutEdge(BaseModel):
    id: str
    type: str  # belt | tap_chain | detour | supply
    item: str
    label: str
    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    tap_index: int | None = None
    self_balance: bool = False
    rule: str | None = None
    note: str | None = None

    model_config = {"populate_by_name": True}


class TapOrderEntry(BaseModel):
    item: str
    label: str
    order: list[str]
    order_labels: list[str]
    rule: str
    explanation: str


class LayoutComputeResponse(BaseModel):
    nodes: list[LayoutNode]
    edges: list[LayoutEdge]
    """无 SBTO 路由的常规产物边，仅用于节点悬停下游子树高亮。"""
    product_edges: list[LayoutEdge] = Field(default_factory=list)
    """被 SBTO 替代的反向树实线，默认不绘制。"""
    hidden_edges: list[LayoutEdge] = Field(default_factory=list)
    tap_orders: list[TapOrderEntry]
    warnings: list[str]
    analysis: dict[str, Any] = Field(default_factory=dict)
    layout_direction: str = "left-to-right"
    history_id: int | None = None
    extensions: dict[str, Any] = Field(
        default_factory=lambda: {
            "blueprint": {"enabled": False, "placeholder": "Phase3 蓝图导出"},
            "throughput": {"enabled": False, "placeholder": "Phase2 产能/机器数"},
            "ratio_robust": {"enabled": False, "placeholder": "不实现随机比例"},
        }
    )


class LayoutHistoryEntry(BaseModel):
    id: int
    save_key: str | None = None
    env_key: str | None = None
    catalog_mode: str
    supply_mode: str
    target_summary: str
    target_count: int
    node_count: int
    edge_count: int
    tap_count: int
    created_at: str


class LayoutHistoryDetail(LayoutHistoryEntry):
    request: dict[str, Any]
    response: dict[str, Any]


class ItemInfo(BaseModel):
    name: str
    label: str
    group: str | None = None
    is_raw: bool = False
    expansion: str | None = None  # base | space-age


class RecipeInfo(BaseModel):
    name: str
    label: str
    category: str
    energy: float
    products: list[dict[str, Any]]
    ingredients: list[dict[str, Any]]
    expansion: str | None = None


class RecipeSearchResponse(BaseModel):
    items: list[ItemInfo]
    recipes: list[RecipeInfo]
    filtered_by_progress: bool = False
    database_source: str = "bundled"


class SaveInfoModel(BaseModel):
    name: str
    path: str
    modified_at: str
    is_last_played: bool
    game_version: str | None = None
    has_cached_progress: bool = False
    needs_reimport: bool = False


class FactorioStatusResponse(BaseModel):
    user_data_dir: str
    saves_dir: str
    executable: str | None
    executable_source: str | None = None
    save_count: int = 0
    last_played_save: str | None
    session_updated_at: str | None
    database_source: str
    progress_loaded: bool
    progress_stale: bool = False
    active_save_key: str | None = None
    enabled_recipe_count: int = 0
    craftable_item_count: int = 0
    has_recipe_pack: bool = False
    pack_count: int = 0


class ItemCatalogResponse(BaseModel):
    all_items: list[ItemInfo] = Field(default_factory=list)
    manufacture_items: list[ItemInfo] = Field(default_factory=list)
    supply_items: list[ItemInfo] = Field(default_factory=list)
    database_source: str = "bundled"
    progress_loaded: bool = False
    progress_stale: bool = False
    active_save_key: str | None = None
    catalog_mode: str = "progress"
    has_recipe_pack: bool = False
    pack_count: int = 0


class PurgeCacheResponse(BaseModel):
    ok: bool
    deleted_packs: int = 0
    deleted_progress: int = 0
    legacy_files_removed: list[str] = Field(default_factory=list)


class LoadProgressRequest(BaseModel):
    save: str
    reexport: bool = False


class ProgressResponse(BaseModel):
    ok: bool
    save: str | None = None
    researched_technology_count: int = 0
    enabled_recipe_count: int = 0
    craftable_items: list[ItemInfo] = Field(default_factory=list)
    manufacture_items: list[ItemInfo] = Field(default_factory=list)
    supply_items: list[ItemInfo] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    database_source: str = "bundled"
    progress_stale: bool = False
    reexported: bool = False
