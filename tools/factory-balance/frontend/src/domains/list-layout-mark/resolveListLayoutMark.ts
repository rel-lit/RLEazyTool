import type { LayoutRequest, LayoutResponse } from "../../api/client";
import {
  inferNodeKind,
  layoutMaxLayer,
  resolveNodeVisual,
} from "../../layout/nodeVisual";
import { normalizeAnalysisSummary } from "../layout-analysis/normalizeAnalysis";
import { nodeByItem } from "../layout-analysis/nodeLookup";
import {
  LIST_LAYOUT_MARK_NONE,
  type ListLayoutMark,
  type ListLayoutMarkRing,
  type ItemListSide,
} from "./types";

/** 直接产物模式：假定外源 */
export const ASSUMED_EXTERNAL_MARK_FILL = "hsla(42, 92%, 56%, 1)";

/** 被剔除终端：固定橙色内盘，不用 layer 中间色 */
export const DEMOTED_OUTPUT_MARK_FILL = "var(--ui-mark-fill-demoted)";

function isExtractRecipe(recipe: string | null | undefined): boolean {
  return !!recipe && recipe.startsWith("fb-extract:");
}

function ringForIntermediateNode(node: LayoutNodeLike): ListLayoutMarkRing {
  const recipe = node.recipe ?? node.meta?.recipe;
  if (isExtractRecipe(recipe)) return "extract";
  return "intermediate";
}

function markDemotedOutput(): ListLayoutMark {
  return {
    kind: "hollow-sphere",
    fill: DEMOTED_OUTPUT_MARK_FILL,
    ring: "demoted",
  };
}

type LayoutNodeLike = NonNullable<ReturnType<typeof nodeByItem>>;

function markWithNodeVisual(
  node: LayoutNodeLike,
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
  node: LayoutNodeLike | undefined,
  effectiveTerminals: readonly string[]
): boolean {
  if (effectiveTerminals.includes(itemName)) return true;
  return node != null && inferNodeKind(node) === "terminal";
}

function isPseudoSupply(
  itemName: string,
  node: LayoutNodeLike | undefined,
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
  const analysis = normalizeAnalysisSummary(layout.analysis);
  if (!analysis || analysis.impossible) {
    return LIST_LAYOUT_MARK_NONE;
  }

  const node = nodeByItem(layout.nodes, itemName);
  const maxLayer = layoutMaxLayer(layout.nodes, analysis.max_layer);

  if (side === "target") {
    if (analysis.demoted_outputs.includes(itemName)) {
      return markDemotedOutput();
    }

    if (isTerminalItem(itemName, node, analysis.effective_terminals) && node) {
      return markWithNodeVisual(node, maxLayer, "terminal");
    }

    if (node && inferNodeKind(node) === "intermediate") {
      return markWithNodeVisual(node, maxLayer, ringForIntermediateNode(node));
    }

    return LIST_LAYOUT_MARK_NONE;
  }

  if (request.forbidden_items?.includes(itemName)) {
    return {
      kind: "hollow-sphere",
      fill: "var(--ui-bg-panel)",
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
    const v = resolveNodeVisual(node, maxLayer);
    const world = node.meta?.supply_kind === "world_baseline";
    return {
      kind: "hollow-sphere",
      fill: world ? "hsla(140, 48%, 22%, 0.9)" : v.background,
      ring: world ? "pure-world" : "pure-solid",
    };
  }

  if (kind === "intermediate") {
    return markWithNodeVisual(node, maxLayer, ringForIntermediateNode(node));
  }

  return LIST_LAYOUT_MARK_NONE;
}
