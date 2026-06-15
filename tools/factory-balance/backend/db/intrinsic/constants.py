"""Intrinsic tag 常量与可抽取资源表。"""

from __future__ import annotations

# Layer IR — resource
IR_INTERNAL = "ir.internal"
IR_EXTRACTABLE = "ir.extractable"
IR_FLUID = "ir.fluid"
IR_ITEM = "ir.item"
IR_CONTAINER_BARREL = "ir.container.barrel"

# Layer IP — recipe
IP_EXTRACT = "ip.extract"
IP_SMELTING = "ip.smelting"
IP_CRAFT = "ip.craft"
IP_CHEMISTRY = "ip.chemistry"
IP_REFINING = "ip.refining"
IP_BARREL_FILL = "ip.barrel.fill"
IP_BARREL_EMPTY = "ip.barrel.empty"
IP_EXCLUDED = "ip.excluded"

CLOSURE_PRIMARY = "primary"
CLOSURE_LOGISTICS = "logistics"
CLOSURE_EXCLUDED = "excluded"

SMELTING_CATEGORIES: frozenset[str] = frozenset({"smelting"})
REFINING_CATEGORIES: frozenset[str] = frozenset(
    {
        "oil-processing",
        "advanced-oil-processing",
        "basic-oil-processing",
        "chemistry",
        "centrifuging",
    }
)
CRAFT_CATEGORIES: frozenset[str] = frozenset(
    {"crafting", "advanced-crafting", "crafting-with-fluid", "electronics", "electronics-machine"}
)


