import type { LayoutNode, LayoutRequest, LayoutResponse } from "../../api/client";
import {
  inferNodeKind,
  layoutMaxLayer,
  resolveNodeVisual,
} from "../../layout/nodeVisual";
import { LIST_LAYOUT_MARK_NONE, type ListLayoutMark, type ItemListSide } from "./types";

/**
 * 列表项—布局关联标记配色：每项样式应对应 pipeline / 分析集的一次判定，
 * 让玩家从侧栏透孔圆环读出「系统如何理解这个物品在本布局中的角色」。
 */

/** 直接产物模式：假定外源（未展开、由模式假定供给） */
export const ASSUMED_EXTERNAL_MARK_FILL = "hsla(42, 92%, 56%, 1)";
export const ASSUMED_EXTERNAL_MARK_RING = "#e3b341";

/** 声明产出被降级为中间物：圈内仍用 layer 色，描边刻意变淡 */
const DEMOTED_OUTPUT_RING = "hsla(230, 11%, 62%, 0.42)";

/** 用户禁止供给且仍出现在本次分析集中：红色虚线空环（圈内不填色） */
const FORBIDDEN_SUPPLY_RING = "#f85149";

function nodeByItem(nodes: LayoutNode[], item: string): LayoutNode | undefined {
  return nodes.find((n) => n.item === item || n.id === item);
}

function markFromNodeVisual(
  node: LayoutNode,
  maxLayer: number,
  ringOverride?: Partial<Pick<ListLayoutMark, "ringColor" | "ringStyle" | "ringWidth">>
): ListLayoutMark {
  const v = resolveNodeVisual(node, maxLayer);
  return {
    kind: "hollow-sphere",
    fill: v.background,
    ringColor: ringOverride?.ringColor ?? v.borderColor,
    ringStyle: ringOverride?.ringStyle ?? v.borderStyle,
    ringWidth: ringOverride?.ringWidth ?? v.borderWidth,
  };
}

function markFromPureSourceNode(node: LayoutNode, maxLayer: number): ListLayoutMark {
  const v = resolveNodeVisual(node, maxLayer);
  const world = node.meta?.supply_kind === "world_baseline";
  return {
    kind: "hollow-sphere",
    fill: world ? "hsla(140, 48%, 22%, 0.9)" : v.background,
    ringColor: v.borderColor,
    ringStyle: v.borderStyle,
    ringWidth: v.borderWidth,
  };
}

function markForbiddenSupply(): ListLayoutMark {
  return {
    kind: "hollow-sphere",
    fill: "transparent",
    ringColor: FORBIDDEN_SUPPLY_RING,
    ringStyle: "dashed",
    ringWidth: "1px",
  };
}

function isTerminalItem(
  itemName: string,
  node: LayoutNode | undefined,
  effectiveTerminals: readonly string[]
): boolean {
  if (effectiveTerminals.includes(itemName)) return true;
  return node != null && inferNodeKind(node) === "terminal";
}

function isPseudoSupply(
  itemName: string,
  node: LayoutNode | undefined,
  pseudoSources: readonly string[]
): boolean {
  if (pseudoSources.includes(itemName)) return true;
  return !!node?.meta?.pseudo_external;
}

/**
 * 由布局快照 + 列表侧推导单个物品的关联标记样式。
 * 仅 UI 展示；不参与排序数据结构。
 */
export function resolveListLayoutMark(
  itemName: string,
  side: ItemListSide,
  layout: LayoutResponse,
  request: LayoutRequest
): ListLayoutMark {
  const node = nodeByItem(layout.nodes, itemName);
  const maxLayer = layoutMaxLayer(layout.nodes);
  const analysis = layout.analysis;

  if (side === "target") {
    const demoted = analysis.demoted_outputs.includes(itemName);

    if (isTerminalItem(itemName, node, analysis.effective_terminals) && node && !demoted) {
      return markFromNodeVisual(node, maxLayer);
    }

    if (node && inferNodeKind(node) === "intermediate") {
      if (demoted) {
        return markFromNodeVisual(node, maxLayer, {
          ringColor: DEMOTED_OUTPUT_RING,
          ringStyle: "solid",
          ringWidth: "1px",
        });
      }
      return markFromNodeVisual(node, maxLayer);
    }

    return LIST_LAYOUT_MARK_NONE;
  }

  if (request.forbidden_items.includes(itemName)) {
    return markForbiddenSupply();
  }

  if (!node) {
    return LIST_LAYOUT_MARK_NONE;
  }

  const kind = inferNodeKind(node);

  if (
    request.supply_mode === "direct" &&
    isPseudoSupply(itemName, node, analysis.pseudo_pure_sources)
  ) {
    return {
      kind: "hollow-sphere",
      fill: ASSUMED_EXTERNAL_MARK_FILL,
      ringColor: ASSUMED_EXTERNAL_MARK_RING,
      ringStyle: "dashed",
      ringWidth: "1px",
    };
  }

  if (kind === "pure_source" && !node.meta?.pseudo_external) {
    return markFromPureSourceNode(node, maxLayer);
  }

  if (kind === "intermediate") {
    return markFromNodeVisual(node, maxLayer);
  }

  return LIST_LAYOUT_MARK_NONE;
}
