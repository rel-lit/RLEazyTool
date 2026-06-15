import type { LayoutEdge } from "../../api/client";

/** 常见流体物品（布局边输送介质 → 管道，否则传送带） */
const FLUID_ITEM_NAMES = new Set([
  "water",
  "crude-oil",
  "petroleum-gas",
  "light-oil",
  "heavy-oil",
  "lubricant",
  "steam",
  "sulfuric-acid",
  "fluoroketone-hot-coolant",
  "fluoroketone-cold-coolant",
  "holmium-solution",
  "electrolyte",
]);

export type FlowEdgeMedium = "传送带" | "管道";

export function isFluidTransportItem(itemName: string): boolean {
  return FLUID_ITEM_NAMES.has(itemName);
}

/** 普通布局边（非 SBTO）的输送介质类型 */
export function flowEdgeMediumLabel(edge: LayoutEdge): FlowEdgeMedium {
  return isFluidTransportItem(edge.item) ? "管道" : "传送带";
}
