import type { Edge } from "@vue-flow/core";
import type { LayoutNode } from "../api/client";
import { EDGE_GAP_PX } from "./sbtoPorts";

function undirectedPair(a: string, b: string): string {
  return a < b ? `${a}|${b}` : `${b}|${a}`;
}

function isSbto(e: Edge): boolean {
  return e.type === "sbto";
}

function isBelt(e: Edge): boolean {
  return e.type === "belt";
}

/** 无向节点对的统一法向（画布左→右），避免 A→B 与 B→A 各自算法向导致同侧重叠。 */
function canonicalPerp(
  idA: string,
  idB: string,
  nodeById: Map<string, LayoutNode>
): { nx: number; ny: number } | null {
  const na = nodeById.get(idA);
  const nb = nodeById.get(idB);
  if (!na || !nb) return null;

  let dx = nb.position.x - na.position.x;
  let dy = nb.position.y - na.position.y;
  if (
    na.position.x > nb.position.x ||
    (na.position.x === nb.position.x && na.position.y > nb.position.y)
  ) {
    dx = -dx;
    dy = -dy;
  }

  const len = Math.hypot(dx, dy) || 1;
  return { nx: -dy / len, ny: dx / len };
}

type GapMeta = {
  pathGapPx: number;
  gapNx?: number;
  gapNy?: number;
  pathCurvature?: number;
};

/**
 * 平行边排斥。
 *
 * 典型重叠：铜线 SBTO 链上「电路板 ↔ 集成电路」虚线段，
 * 与产物实线「电路板 → 集成电路」共用同一对节点（同向或反向）。
 */
export function assignEdgeGaps(
  edges: Edge[],
  nodeById: Map<string, LayoutNode> = new Map()
): Edge[] {
  const gapById = new Map<string, GapMeta>();
  const byUndirected = new Map<string, Edge[]>();

  for (const e of edges) {
    if (!e.source || !e.target) continue;
    const key = undirectedPair(e.source, e.target);
    const list = byUndirected.get(key) ?? [];
    list.push(e);
    byUndirected.set(key, list);
  }

  for (const [key, list] of byUndirected.entries()) {
    if (list.length <= 1) continue;

    const [idA, idB] = key.split("|");
    const perp = canonicalPerp(idA, idB, nodeById);

    const sbtoEdges = list.filter(isSbto);
    const beltEdges = list.filter(isBelt);

    if (sbtoEdges.length > 0 && beltEdges.length > 0) {
      const half = EDGE_GAP_PX / 2;
      let paired = false;

      for (const s of sbtoEdges) {
        for (const b of beltEdges) {
          const sameDir =
            s.source === b.source && s.target === b.target;
          const oppDir =
            s.source === b.target && s.target === b.source;
          if (!sameDir && !oppDir) continue;

          paired = true;
          gapById.set(s.id, {
            pathGapPx: half,
            gapNx: perp?.nx,
            gapNy: perp?.ny,
            pathCurvature: 0.35,
          });
          gapById.set(b.id, {
            pathGapPx: -half,
            gapNx: perp?.nx,
            gapNy: perp?.ny,
            pathCurvature: -0.35,
          });
        }
      }

      if (paired) continue;
    }

    if (list.length >= 2) {
      const sorted = [...list].sort((a, b) => a.id.localeCompare(b.id));
      const mid = (sorted.length - 1) / 2;
      sorted.forEach((e, i) =>
        gapById.set(e.id, {
          pathGapPx: (i - mid) * EDGE_GAP_PX,
          gapNx: perp?.nx,
          gapNy: perp?.ny,
        })
      );
    }
  }

  return edges.map((e) => {
    const meta = gapById.get(e.id);
    if (!meta) return e;
    return {
      ...e,
      data: {
        ...(e.data as object),
        pathGapPx: meta.pathGapPx,
        ...(meta.gapNx != null && meta.gapNy != null
          ? { gapNx: meta.gapNx, gapNy: meta.gapNy }
          : {}),
        ...(meta.pathCurvature != null
          ? { pathCurvature: meta.pathCurvature }
          : {}),
      },
    };
  });
}
