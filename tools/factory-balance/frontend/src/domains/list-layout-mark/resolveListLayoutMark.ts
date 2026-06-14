import type { LayoutNode, LayoutRequest, LayoutResponse } from "../../api/client";
import {
  inferNodeKind,
  layoutMaxLayer,
  resolveNodeVisual,
} from "../../layout/nodeVisual";
import { LIST_LAYOUT_MARK_NONE, type ListLayoutMark, type ItemListSide } from "./types";

/** 直接产物模式：假定外源（列表标记专用橙黄；画布节点后续可对齐） */
export const ASSUMED_EXTERNAL_MARK_FILL = "hsla(42, 92%, 56%, 1)";
export const ASSUMED_EXTERNAL_MARK_RING = "#e3b341";

function nodeByItem(nodes: LayoutNode[], item: string): LayoutNode | undefined {
  return nodes.find((n) => n.item === item || n.id === item);
}

function markFromNodeVisual(node: LayoutNode, maxLayer: number): ListLayoutMark {
  const v = resolveNodeVisual(node, maxLayer);
  return {
    kind: "hollow-sphere",
    fill: v.background,
    ringColor: v.borderColor,
    ringStyle: v.borderStyle,
    ringWidth: v.borderWidth,
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
    if (isTerminalItem(itemName, node, analysis.effective_terminals) && node) {
      return markFromNodeVisual(node, maxLayer);
    }
    if (node && inferNodeKind(node) === "intermediate") {
      return markFromNodeVisual(node, maxLayer);
    }
    return LIST_LAYOUT_MARK_NONE;
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
