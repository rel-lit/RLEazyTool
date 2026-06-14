import type { ItemInfo, LayoutRequest, LayoutResponse } from "../../api/client";
import { inferNodeKind } from "../../layout/nodeVisual";
import { normalizeAnalysisSummary } from "./normalizeAnalysis";
import { nodeByItem, nodeMetrics } from "./nodeLookup";
import type { ItemListSortKey, NormalizedAnalysisSummary } from "./types";

/** 产出列表：有效终端 → 链上中间物 → 被降级终端 → 其余分析集 */
export const TARGET_LIST_TIER = {
  EFFECTIVE_TERMINAL: 0,
  INTERMEDIATE: 1,
  DEMOTED: 2,
  OTHER: 3,
  OUTSIDE: 99,
} as const;

/** 供给列表：禁止 → 已知供给 → 假定外源 → 世界底层 → 其它外源 → 中间物 */
export const SUPPLY_LIST_TIER = {
  FORBIDDEN: 0,
  USER_SUPPLIED: 1,
  ASSUMED_PSEUDO: 2,
  PURE_WORLD: 3,
  PURE_SOLID: 4,
  INTERMEDIATE: 5,
  OTHER: 6,
  OUTSIDE: 99,
} as const;

function isPseudoSupply(
  itemName: string,
  node: ReturnType<typeof nodeByItem>,
  pseudoSources: readonly string[]
): boolean {
  if (pseudoSources.includes(itemName)) return true;
  return !!node?.meta?.pseudo_external;
}

export function resolveTargetListTier(
  itemName: string,
  layout: LayoutResponse,
  analysis: NormalizedAnalysisSummary
): number {
  if (!analysis.analysis_items.includes(itemName)) {
    if (analysis.demoted_outputs.includes(itemName)) {
      return TARGET_LIST_TIER.DEMOTED;
    }
    return TARGET_LIST_TIER.OUTSIDE;
  }
  if (analysis.effective_terminals.includes(itemName)) {
    return TARGET_LIST_TIER.EFFECTIVE_TERMINAL;
  }
  if (analysis.demoted_outputs.includes(itemName)) {
    return TARGET_LIST_TIER.DEMOTED;
  }
  const node = nodeByItem(layout.nodes, itemName);
  if (node && inferNodeKind(node) === "intermediate") {
    return TARGET_LIST_TIER.INTERMEDIATE;
  }
  return TARGET_LIST_TIER.OTHER;
}

export function resolveSupplyListTier(
  itemName: string,
  layout: LayoutResponse,
  request: LayoutRequest,
  analysis: NormalizedAnalysisSummary
): number {
  if (!analysis.analysis_items.includes(itemName)) {
    return SUPPLY_LIST_TIER.OUTSIDE;
  }
  if (request.forbidden_items?.includes(itemName)) {
    return SUPPLY_LIST_TIER.FORBIDDEN;
  }
  const node = nodeByItem(layout.nodes, itemName);
  if (!node) return SUPPLY_LIST_TIER.OTHER;

  const kind = inferNodeKind(node);

  if (
    request.supply_mode === "direct" &&
    isPseudoSupply(itemName, node, analysis.pseudo_pure_sources)
  ) {
    return SUPPLY_LIST_TIER.ASSUMED_PSEUDO;
  }

  if (request.supplied_items?.includes(itemName) && kind === "pure_source") {
    return SUPPLY_LIST_TIER.USER_SUPPLIED;
  }

  if (kind === "pure_source" && !node.meta?.pseudo_external) {
    if (node.meta?.supply_kind === "world_baseline") {
      return SUPPLY_LIST_TIER.PURE_WORLD;
    }
    return SUPPLY_LIST_TIER.PURE_SOLID;
  }

  if (kind === "intermediate") {
    return SUPPLY_LIST_TIER.INTERMEDIATE;
  }

  return SUPPLY_LIST_TIER.OTHER;
}

export function resolveTargetListSortKey(
  item: ItemInfo,
  layout: LayoutResponse,
  _request: LayoutRequest
): ItemListSortKey {
  const analysis = normalizeAnalysisSummary(layout.analysis);
  const tier = analysis
    ? resolveTargetListTier(item.name, layout, analysis)
    : TARGET_LIST_TIER.OUTSIDE;
  const metrics = nodeMetrics(nodeByItem(layout.nodes, item.name));
  return {
    tier,
    layer: metrics.layer,
    rank: metrics.rank,
    rankFrac: metrics.rankFrac,
    label: item.label,
    name: item.name,
  };
}

export function resolveSupplyListSortKey(
  item: ItemInfo,
  layout: LayoutResponse,
  request: LayoutRequest
): ItemListSortKey {
  const analysis = normalizeAnalysisSummary(layout.analysis);
  const tier = analysis
    ? resolveSupplyListTier(item.name, layout, request, analysis)
    : SUPPLY_LIST_TIER.OUTSIDE;
  const metrics = nodeMetrics(nodeByItem(layout.nodes, item.name));
  return {
    tier,
    layer: metrics.layer,
    rank: metrics.rank,
    rankFrac: metrics.rankFrac,
    label: item.label,
    name: item.name,
  };
}

export function compareTargetListSortKeys(a: ItemListSortKey, b: ItemListSortKey): number {
  if (a.tier !== b.tier) return a.tier - b.tier;
  if (a.layer !== b.layer) return b.layer - a.layer;
  if (a.rank !== b.rank) return a.rank - b.rank;
  if (a.rankFrac !== b.rankFrac) return a.rankFrac - b.rankFrac;
  const byLabel = a.label.localeCompare(b.label, "zh-CN");
  if (byLabel !== 0) return byLabel;
  return a.name.localeCompare(b.name);
}

export function compareSupplyListSortKeys(a: ItemListSortKey, b: ItemListSortKey): number {
  if (a.tier !== b.tier) return a.tier - b.tier;
  if (a.layer !== b.layer) return a.layer - b.layer;
  if (a.rank !== b.rank) return a.rank - b.rank;
  if (a.rankFrac !== b.rankFrac) return a.rankFrac - b.rankFrac;
  const byLabel = a.label.localeCompare(b.label, "zh-CN");
  if (byLabel !== 0) return byLabel;
  return a.name.localeCompare(b.name);
}

export function createTargetSortKeyResolver(snapshot: {
  layout: LayoutResponse;
  request: LayoutRequest;
}): (item: ItemInfo) => ItemListSortKey {
  return (item) => resolveTargetListSortKey(item, snapshot.layout, snapshot.request);
}

export function createSupplySortKeyResolver(snapshot: {
  layout: LayoutResponse;
  request: LayoutRequest;
}): (item: ItemInfo) => ItemListSortKey {
  return (item) => resolveSupplyListSortKey(item, snapshot.layout, snapshot.request);
}
