import type { LayoutNode } from "../../api/client";

export function nodeByItem(
  nodes: readonly LayoutNode[],
  item: string
): LayoutNode | undefined {
  return nodes.find((n) => n.item === item || n.id === item);
}

export function nodeMetrics(node: LayoutNode | undefined): {
  layer: number;
  rank: number;
  rankFrac: number;
} {
  if (!node) {
    return { layer: -1, rank: 0, rankFrac: 0 };
  }
  return {
    layer: node.layer ?? node.meta?.layer ?? -1,
    rank: node.meta?.rank ?? 0,
    rankFrac: node.meta?.rank_frac ?? 0,
  };
}
