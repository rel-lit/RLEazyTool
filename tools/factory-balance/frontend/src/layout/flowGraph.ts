import type { Edge, Node } from "@vue-flow/core";
import type { LayoutEdge, LayoutNode } from "../api/client";
import { assignEdgeGaps } from "./edgePathGap";
import { isSbtoEdge } from "./focus";
import { assignSbtoBadgeColors } from "./itemColors";
import { buildSbtoChainRanks, sbtoFlowSignForEdge } from "./sbtoFlow";
import { beltHandleIds, sbtoHandleIds } from "./sbtoPorts";

export const SBTO_STROKE = "#b1bac4";
export const BELT_STROKE = "#9aa4af";

export type FactoryNodeData = LayoutNode;

export function factoryNodeLabel(n: LayoutNode): string {
  if (n.meta?.external_leaf && !n.meta?.pseudo_external) {
    return `⛏ ${n.label}`;
  }
  return n.label;
}

function edgeTapLabel(e: LayoutEdge): string {
  if (!isSbtoEdge(e) || e.tap_index == null) return "";
  return String(e.tap_index);
}

/** 布局重算：preserve=false 时使用服务端坐标（严格重算） */
export function mergeLayoutNodes(
  layoutNodes: LayoutNode[],
  current: Node[],
  preserve = true
): Node[] {
  const posById = preserve
    ? new Map(current.map((n) => [n.id, n.position]))
    : new Map<string, { x: number; y: number }>();
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
  const sbtoItems = layoutEdges.filter(isSbtoEdge).map((e) => e.item);
  const badgeColors = assignSbtoBadgeColors(sbtoItems);
  const chainRanks = buildSbtoChainRanks(layoutEdges);

  const visible = layoutEdges.map((e) =>
    edgeToFlow(e, selectedEdgeId, nodeById, badgeColors, chainRanks)
  );
  const hidden = overlayHidden.map((e) => hiddenEdgeToFlow(e, nodeById));
  return assignEdgeGaps([...visible, ...hidden], nodeById);
}

function nodeGrade(nodeById: Map<string, LayoutNode>, id: string): number {
  return nodeById.get(id)?.layer ?? 0;
}

function edgeToFlow(
  e: LayoutEdge,
  selectedEdgeId: string | null,
  nodeById: Map<string, LayoutNode>,
  badgeColors: Map<string, string>,
  chainRanks: Map<string, Map<string, number>>
): Edge {
  const selected = selectedEdgeId === e.id;
  if (isSbtoEdge(e)) {
    const fromG = nodeGrade(nodeById, e.from);
    const toG = nodeGrade(nodeById, e.to);
    const ports = sbtoHandleIds(
      fromG,
      toG,
      nodeById.get(e.from),
      nodeById.get(e.to)
    );
    return {
      id: e.id,
      type: "sbto",
      source: e.from,
      target: e.to,
      sourceHandle: ports.sourceHandle,
      targetHandle: ports.targetHandle,
      data: {
        layoutEdge: e,
        badgeColor: badgeColors.get(e.item) ?? "#58a6ff",
        tapLabel: edgeTapLabel(e),
        fromGrade: fromG,
        toGrade: toG,
        flowSign: sbtoFlowSignForEdge(e, chainRanks),
      },
      style: {
        stroke: SBTO_STROKE,
        strokeWidth: selected ? 3 : 2.5,
        strokeDasharray: "10 6",
        opacity: 1,
      },
    };
  }
  const belt = beltHandleIds(nodeById.get(e.from), nodeById.get(e.to));
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
  const belt = beltHandleIds(nodeById.get(e.from), nodeById.get(e.to));
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
