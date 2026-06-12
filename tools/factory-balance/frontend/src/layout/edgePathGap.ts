import type { Edge } from "@vue-flow/core";
import { EDGE_GAP_PX } from "./sbtoPorts";

function sortEdges(list: Edge[]): Edge[] {
  return [...list].sort((a, b) => {
    const ta = a.type === "sbto" ? 0 : 1;
    const tb = b.type === "sbto" ? 0 : 1;
    if (ta !== tb) return ta - tb;
    const sa = a.source ?? "";
    const sb = b.source ?? "";
    if (sa !== sb) return sa.localeCompare(sb);
    return a.id.localeCompare(b.id);
  });
}

function applyGroupGap(
  gapById: Map<string, number>,
  list: Edge[],
  gapPx: number
): void {
  if (list.length <= 1) return;
  const sorted = sortEdges(list);
  const mid = (sorted.length - 1) / 2;
  sorted.forEach((e, i) => {
    const next = (i - mid) * gapPx;
    const prev = gapById.get(e.id);
    if (prev == null || Math.abs(next) > Math.abs(prev)) {
      gapById.set(e.id, next);
    }
  });
}

/**
 * 平行边排斥：同 source→target，以及汇入同一 target 的多条边（如内燃机/电路板→集成电路）。
 */
export function assignEdgeGaps(edges: Edge[]): Edge[] {
  const byEndpoints = new Map<string, Edge[]>();
  const byTarget = new Map<string, Edge[]>();

  for (const e of edges) {
    if (!e.source || !e.target) continue;
    const pair = `${e.source}|${e.target}`;
    const ep = byEndpoints.get(pair) ?? [];
    ep.push(e);
    byEndpoints.set(pair, ep);

    const tg = byTarget.get(e.target) ?? [];
    tg.push(e);
    byTarget.set(e.target, tg);
  }

  const gapById = new Map<string, number>();

  for (const list of byEndpoints.values()) {
    applyGroupGap(gapById, list, EDGE_GAP_PX);
  }
  for (const list of byTarget.values()) {
    applyGroupGap(gapById, list, EDGE_GAP_PX * 0.85);
  }

  return edges.map((e) => {
    const pathGapPx = gapById.get(e.id);
    if (pathGapPx == null) return e;
    return {
      ...e,
      data: { ...(e.data as object), pathGapPx },
    };
  });
}
