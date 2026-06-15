import type { LayoutNode, LayoutRequest, LayoutResponse } from "../../api/client";
import { inferNodeKind } from "../../layout/nodeVisual";
import { normalizeAnalysisSummary } from "../layout-analysis/normalizeAnalysis";
import { nodeByItem } from "../layout-analysis/nodeLookup";
import type { ListLayoutMarkRing } from "./types";
import { resolveListLayoutMark } from "./resolveListLayoutMark";

/** 与列表镂空环 rim 语义一一对应的中文标签 */
export const NODE_RING_LABELS: Readonly<Record<ListLayoutMarkRing, string>> = {
  terminal: "有效终端",
  demoted: "被降级声明终端",
  intermediate: "中间产物",
  extract: "抽取中间产物",
  "pure-solid": "外源（固体）",
  "pure-world": "世界基准外源",
  assumed: "假定外源",
  forbidden: "禁止供给",
};

export function labelForNodeRing(ring: ListLayoutMarkRing): string {
  return NODE_RING_LABELS[ring];
}

function fallbackKindLabel(node: LayoutNode): string {
  const kind = inferNodeKind(node);
  if (kind === "terminal") return NODE_RING_LABELS.terminal;
  if (kind === "pure_source") return NODE_RING_LABELS["pure-solid"];
  const recipe = node.recipe ?? node.meta?.recipe;
  if (recipe?.startsWith("fb-extract:")) return NODE_RING_LABELS.extract;
  return NODE_RING_LABELS.intermediate;
}

/**
 * 画布检视 / 信息栏：解析节点在布局中的参与角色（对齐 list-layout-mark 镂空环类型）。
 * 先尝试产出侧标记，再尝试供给侧；均无时回退 node_kind 推断。
 */
export function resolveNodeRingRoleLabel(
  itemName: string,
  layout: LayoutResponse,
  request?: LayoutRequest | null
): string {
  const node = nodeByItem(layout.nodes, itemName);
  const req: LayoutRequest =
    request ??
    ({
      targets: [],
      supply_mode: "raw",
      supplied_items: [],
      forbidden_items: [],
      catalog_mode: "progress",
      layout_options: {
        primary_direction: "left-to-right",
        buffer_recommendation: true,
      },
    } satisfies LayoutRequest);

  const targetMark = resolveListLayoutMark(itemName, "target", layout, req);
  if (targetMark.kind === "hollow-sphere") {
    return labelForNodeRing(targetMark.ring);
  }

  const supplyMark = resolveListLayoutMark(itemName, "supply", layout, req);
  if (supplyMark.kind === "hollow-sphere") {
    return labelForNodeRing(supplyMark.ring);
  }

  if (node) return fallbackKindLabel(node);

  const analysis = normalizeAnalysisSummary(layout.analysis);
  if (analysis?.demoted_outputs.includes(itemName)) {
    return NODE_RING_LABELS.demoted;
  }

  return "布局外物品";
}
