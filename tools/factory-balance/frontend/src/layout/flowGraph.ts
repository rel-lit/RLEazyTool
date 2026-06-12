import type { Edge, Node } from "@vue-flow/core";
import type { LayoutEdge, LayoutNode } from "../api/client";
import { assignEdgeGaps } from "./edgePathGap";
import { isSbtoEdge } from "./focusGraph";
import { itemEdgeColor } from "./itemColors";
import { beltHandleIds, sbtoHandleIds } from "./sbtoPorts";

export const SBTO_STROKE = "#b1bac4";
export const BELT_STROKE = "#9aa4af";

export type FactoryNodeData = LayoutNode;

export function factoryNodeClass(n: LayoutNode): string {
  const parts = ["fb-node", `fb-node--${n.type}`];
  if (n.type === "supply" && n.meta?.supply_kind === "world_baseline") {
    parts.push("fb-node--world-baseline");
  }
  if (n.meta?.role === "world_extract") {
    parts.push("fb-node--world-extract");
  }
  return parts.join(" ");
}

export function factoryNodeLabel(n: LayoutNode): string {
  if (n.type === "supply" && n.meta?.supply_kind === "world_baseline") {
    return `⛏ ${n.label}`;
  }
  if (n.meta?.role === "world_extract") {
    return `⛏ ${n.label}`;
  }
  return n.label;
}

function edgeTapLabel(e: LayoutEdge): string {
  if (!isSbtoEdge(e) || e.tap_index == null) return "";
  return String(e.tap_index);
}

/** 布局重算：合并新坐标，保留用户已拖动的 position */
export function mergeLayoutNodes(
  layoutNodes: LayoutNode[],
  current: Node[]
): Node[] {
  const posById = new Map(current.map((n) => [n.id, n.position]));
  return layoutNodes.map((n) => ({
    id: n.id,
    type: "factory" as const,
    position: posById.get(n.id) ?? { x: n.position.x, y: n.position.y },
    data: { ...n } satisfies FactoryNodeData,
  }));
}

export function buildFlowEdges(
  layoutEdges: LayoutEdge[],
  selectedEdgeId: string | null,
  overlayHidden: LayoutEdge[] = [],
  nodeById: Map<string, LayoutNode> = new Map()
): Edge[] {
  const visible = layoutEdges.map((e) =>
    edgeToFlow(e, selectedEdgeId, nodeById)
  );
  const hidden = overlayHidden.map((e) => hiddenEdgeToFlow(e, nodeById));
  return assignEdgeGaps([...visible, ...hidden]);
}

function nodeGrade(nodeById: Map<string, LayoutNode>, id: string): number {
  return nodeById.get(id)?.layer ?? 0;
}

function edgeToFlow(
  e: LayoutEdge,
  selectedEdgeId: string | null,
  nodeById: Map<string, LayoutNode>
): Edge {
  const selected = selectedEdgeId === e.id;
  if (isSbtoEdge(e)) {
    const fromG = nodeGrade(nodeById, e.from);
    const toG = nodeGrade(nodeById, e.to);
    const ports = sbtoHandleIds(fromG, toG);
    return {
      id: e.id,
      type: "sbto",
      source: e.from,
      target: e.to,
      sourceHandle: ports.sourceHandle,
      targetHandle: ports.targetHandle,
      data: {
        layoutEdge: e,
        badgeColor: itemEdgeColor(e.item),
        tapLabel: edgeTapLabel(e),
        fromGrade: fromG,
        toGrade: toG,
      },
      style: {
        stroke: SBTO_STROKE,
        strokeWidth: selected ? 3 : 2.5,
        strokeDasharray: "10 6",
        opacity: 1,
      },
    };
  }
  const belt = beltHandleIds();
  return {
    id: e.id,
    type: "belt",
    source: e.from,
    target: e.to,
    sourceHandle: belt.sourceHandle,
    targetHandle: belt.targetHandle,
    data: { layoutEdge: e },
    style: {
      stroke: BELT_STROKE,
      strokeWidth: selected ? 2.5 : 2,
      opacity: 1,
    },
  };
}

function hiddenEdgeToFlow(
  e: LayoutEdge,
  nodeById: Map<string, LayoutNode>
): Edge {
  const belt = beltHandleIds();
  return {
    id: e.id,
    type: "belt",
    source: e.from,
    target: e.to,
    sourceHandle: belt.sourceHandle,
    targetHandle: belt.targetHandle,
    selectable: false,
    focusable: false,
    data: { layoutEdge: e, isHiddenOverlay: true },
    style: {
      stroke: BELT_STROKE,
      strokeWidth: 2,
      opacity: 1,
    },
    zIndex: 0,
  };
}
