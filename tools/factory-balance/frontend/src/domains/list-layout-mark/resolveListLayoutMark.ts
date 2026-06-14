import type { LayoutNode, LayoutRequest, LayoutResponse } from "../../api/client";
import {
  inferNodeKind,
  layoutMaxLayer,
  resolveNodeVisual,
} from "../../layout/nodeVisual";
import { LIST_LAYOUT_MARK_NONE, type ListLayoutMark, type ItemListSide } from "./types";

/**
 * 列表项—布局关联标记：圈内 fill 反映 pipeline 判定；圆环统一为细铁环（CSS），
 * 仅 demoted / forbidden / assumed 使用线框变体。
 */

/** 直接产物模式：假定外源（未展开、由模式假定供给） */
export const ASSUMED_EXTERNAL_MARK_FILL = "hsla(42, 92%, 56%, 1)";

function nodeByItem(nodes: LayoutNode[], item: string): LayoutNode | undefined {
  return nodes.find((n) => n.item === item || n.id === item);
}

function markWithFill(
  node: LayoutNode,
  maxLayer: number,
  ring: ListLayoutMark["ring"] = "default"
): ListLayoutMark {
  const v = resolveNodeVisual(node, maxLayer);
  return {
    kind: "hollow-sphere",
    fill: v.background,
    ring,
  };
}

function markFromPureSourceNode(node: LayoutNode, maxLayer: number): ListLayoutMark {
  const v = resolveNodeVisual(node, maxLayer);
  const world = node.meta?.supply_kind === "world_baseline";
  return {
    kind: "hollow-sphere",
    fill: world ? "hsla(140, 48%, 22%, 0.9)" : v.background,
    ring: "default",
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
      return markWithFill(node, maxLayer);
    }

    if (node && inferNodeKind(node) === "intermediate") {
      return markWithFill(node, maxLayer, demoted ? "demoted" : "default");
    }

    return LIST_LAYOUT_MARK_NONE;
  }

  if (request.forbidden_items.includes(itemName)) {
    return {
      kind: "hollow-sphere",
      fill: "transparent",
      ring: "forbidden",
    };
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
      ring: "assumed",
    };
  }

  if (kind === "pure_source" && !node.meta?.pseudo_external) {
    return markFromPureSourceNode(node, maxLayer);
  }

  if (kind === "intermediate") {
    return markWithFill(node, maxLayer);
  }

  return LIST_LAYOUT_MARK_NONE;
}
