import type { LayoutEdge } from "../api/client";
import { isSbtoEdge } from "./focus";

/**
 * SBTO 链在 backend 按 tap_index 串成：producer → order[0] → order[1] …
 * order[0] 为最高优先级。动画沿链的「带内流向」（tap_index 递增方向），
 * 不是指向更高优先级节点（那会是链的上游，与几何 from→to 常相反）。
 */

export function chainRanksForItem(
  item: string,
  edges: LayoutEdge[]
): Map<string, number> {
  const segs = edges
    .filter((e) => e.item === item && isSbtoEdge(e))
    .sort((a, b) => (a.tap_index ?? 0) - (b.tap_index ?? 0));

  const ranks = new Map<string, number>();
  let r = 0;
  for (const e of segs) {
    if (!ranks.has(e.from)) ranks.set(e.from, r++);
    if (!ranks.has(e.to)) ranks.set(e.to, r++);
  }
  return ranks;
}

export function buildSbtoChainRanks(
  edges: LayoutEdge[]
): Map<string, Map<string, number>> {
  const byItem = new Map<string, Map<string, number>>();
  const items = new Set(
    edges.filter(isSbtoEdge).map((e) => e.item)
  );
  for (const item of items) {
    byItem.set(item, chainRanksForItem(item, edges));
  }
  return byItem;
}

/** 沿链序：rank(to) > rank(from) 则虚线正向流动 */
export function sbtoFlowSignForEdge(
  edge: LayoutEdge,
  chainRanks: Map<string, Map<string, number>>
): 1 | -1 {
  const ranks = chainRanks.get(edge.item);
  if (!ranks) return 1;
  const rf = ranks.get(edge.from);
  const rt = ranks.get(edge.to);
  if (rf == null || rt == null) return 1;
  if (rt > rf) return 1;
  if (rt < rf) return -1;
  return 1;
}
