import type { LayoutNode, LayoutRequest, LayoutResponse } from "../../api/client";
import {
  inferNodeKind,
  layoutMaxLayer,
  resolveNodeVisual,
} from "../../layout/nodeVisual";
import {
  LIST_LAYOUT_MARK_NONE,
  type ListLayoutMark,
  type ListLayoutMarkRing,
  type ItemListSide,
} from "./types";

/** 直接产物模式：假定外源 */
export const ASSUMED_EXTERNAL_MARK_FILL = "hsla(42, 92%, 56%, 1)";

function nodeByItem(nodes: LayoutNode[], item: string): LayoutNode | undefined {
  return nodes.find((n) => n.item === item || n.id === item);
}

function isExtractRecipe(recipe: string | null | undefined): boolean {
  return !!recipe && recipe.startsWith("fb-extract:");
}

function ringForIntermediateNode(
  node: LayoutNode,
  demoted: boolean
): ListLayoutMarkRing {
  if (demoted) return "demoted";
  const recipe = node.recipe ?? node.meta?.recipe;
  if (isExtractRecipe(recipe)) return "extract";
  return "intermediate";
}

function markWithNodeVisual(
  node: LayoutNode,
  maxLayer: number,
  ring: ListLayoutMarkRing
): ListLayoutMark {
  const v = resolveNodeVisual(node, maxLayer);
  return {
    kind: "hollow-sphere",
    fill: v.background,
    ring,
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

export function resolveListLayoutMark(
  itemName: string,
  side: ItemListSide,
  layout: LayoutResponse,
  request: LayoutRequest
): ListLayoutMark {
  const node = nodeByItem(layout.nodes, itemName);
  const maxLayer = layoutMaxLayer(layout.nodes);
  const analysis = layout.analysis;
  if (!analysis) {
    return LIST_LAYOUT_MARK_NONE;
  }

  if (side === "target") {
    const demoted = analysis.demoted_outputs?.includes(itemName) ?? false;

    if (
      isTerminalItem(itemName, node, analysis.effective_terminals ?? []) &&
      node &&
      !demoted
    ) {
      return markWithNodeVisual(node, maxLayer, "terminal");
    }

    if (node && inferNodeKind(node) === "intermediate") {
      return markWithNodeVisual(
        node,
        maxLayer,
        ringForIntermediateNode(node, demoted)
      );
    }

    return LIST_LAYOUT_MARK_NONE;
  }

  if (request.forbidden_items?.includes(itemName)) {
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
    isPseudoSupply(itemName, node, analysis.pseudo_pure_sources ?? [])
  ) {
    return {
      kind: "hollow-sphere",
      fill: ASSUMED_EXTERNAL_MARK_FILL,
      ring: "assumed",
    };
  }

  if (kind === "pure_source" && !node.meta?.pseudo_external) {
    const v = resolveNodeVisual(node, maxLayer);
    const world = node.meta?.supply_kind === "world_baseline";
    return {
      kind: "hollow-sphere",
      fill: world ? "hsla(140, 48%, 22%, 0.9)" : v.background,
      ring: world ? "pure-world" : "pure-solid",
    };
  }

  if (kind === "intermediate") {
    return markWithNodeVisual(node, maxLayer, ringForIntermediateNode(node, false));
  }

  return LIST_LAYOUT_MARK_NONE;
}
