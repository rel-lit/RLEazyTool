import type { LayoutEdge, LayoutNode } from "../api/client";
import {
  buildProductGraph,
  dependencySubtree,
  directDownstreamHop,
  indexBeltIds,
  indexEdgesByKey,
  isMergeNode,
  mapProductEdgesToLayout,
  mergeNodeHiddenFanout,
  sbtoItemsFromNode,
} from "./productGraph";

export type FocusMode = "node-subtree" | "edge";

export interface FocusHighlight {
  nodeIds: Set<string>;
  edgeIds: Set<string>;
  hiddenEdgeIds: Set<string>;
  dimSbtoItems: Set<string>;
  sbtoItem: string | null;
  mode: FocusMode;
}

export function isSbtoEdge(e: LayoutEdge): boolean {
  return e.type === "tap_chain" || e.type === "detour";
}

export function isHiddenEdge(e: LayoutEdge): boolean {
  return e.type === "hidden";
}

export function isFlowEdge(e: LayoutEdge): boolean {
  return e.type === "belt";
}

export function focusFromNode(
  nodeId: string,
  productEdges: LayoutEdge[],
  hiddenEdges: LayoutEdge[],
  layoutEdges: LayoutEdge[],
  _nodes: LayoutNode[]
): FocusHighlight {
  const graph = buildProductGraph(productEdges);
  const beltIds = indexBeltIds(layoutEdges);
  const hiddenByKey = indexEdgesByKey(hiddenEdges);

  const up = dependencySubtree(graph, nodeId);
  const down = directDownstreamHop(graph, nodeId);

  const nodeIds = new Set<string>([nodeId, ...up.nodeIds, ...down.nodeIds]);
  const productEdgeIds = new Set<string>([
    ...up.productEdgeIds,
    ...down.productEdgeIds,
  ]);

  const mapped = mapProductEdgesToLayout(
    productEdgeIds,
    graph,
    beltIds,
    hiddenByKey
  );

  const edgeIds = new Set<string>(mapped.beltEdgeIds);
  const hiddenEdgeIds = new Set<string>(mapped.hiddenEdgeIds);
  const dimSbtoItems = new Set<string>();

  if (isMergeNode(nodeId, hiddenEdges)) {
    const fan = mergeNodeHiddenFanout(nodeId, hiddenEdges);
    for (const id of fan.nodeIds) nodeIds.add(id);
    for (const id of fan.hiddenEdgeIds) hiddenEdgeIds.add(id);
    for (const item of sbtoItemsFromNode(nodeId, hiddenEdges)) {
      dimSbtoItems.add(item);
    }
  }

  return {
    nodeIds,
    edgeIds,
    hiddenEdgeIds,
    dimSbtoItems,
    sbtoItem: null,
    mode: "node-subtree",
  };
}

export function focusFromEdge(
  edge: LayoutEdge,
  edges: LayoutEdge[]
): FocusHighlight {
  if (isSbtoEdge(edge)) {
    const nodeIds = new Set<string>();
    const edgeIds = new Set<string>();
    for (const e of edges) {
      if (e.item === edge.item && isSbtoEdge(e)) {
        edgeIds.add(e.id);
        nodeIds.add(e.from);
        nodeIds.add(e.to);
      }
    }
    return {
      nodeIds,
      edgeIds,
      hiddenEdgeIds: new Set(),
      dimSbtoItems: new Set(),
      sbtoItem: edge.item,
      mode: "edge",
    };
  }

  return {
    nodeIds: new Set([edge.from, edge.to]),
    edgeIds: new Set([edge.id]),
    hiddenEdgeIds: new Set(),
    dimSbtoItems: new Set(),
    sbtoItem: null,
    mode: "edge",
  };
}

export function isNodeHighlighted(
  nodeId: string,
  focus: FocusHighlight | null
): boolean {
  if (!focus) return true;
  return focus.nodeIds.has(nodeId);
}

export function isEdgeHighlighted(
  edge: LayoutEdge,
  focus: FocusHighlight | null
): boolean {
  if (!focus) return true;
  if (isHiddenEdge(edge)) {
    return focus.hiddenEdgeIds.has(edge.id);
  }
  if (isSbtoEdge(edge)) {
    if (focus.mode === "node-subtree") {
      return false;
    }
    return focus.edgeIds.has(edge.id);
  }
  return focus.edgeIds.has(edge.id);
}

export function sbtoFlowActive(
  edge: LayoutEdge,
  focus: FocusHighlight | null
): boolean {
  if (!focus?.sbtoItem || focus.mode !== "edge") return false;
  return (
    isSbtoEdge(edge) &&
    edge.item === focus.sbtoItem &&
    focus.edgeIds.has(edge.id)
  );
}
