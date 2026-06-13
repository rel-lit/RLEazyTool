import { ref, watch, type Ref } from "vue";
import type { Edge, Node } from "@vue-flow/core";
import type { AppEventBus } from "../app/events";
import type { LayoutEdge, LayoutNode } from "../api/client";
import { buildFlowEdges, mergeLayoutNodes, applyConnectedHandlesToNodes } from "./flowGraph";
import type { FocusHighlight } from "./focus";

export interface CanvasLayoutProps {
  nodes: Ref<LayoutNode[]>;
  edges: Ref<LayoutEdge[]>;
  hiddenEdges: Ref<LayoutEdge[]>;
  selectedEdgeId: Ref<string | null>;
  highlight: Ref<FocusHighlight | null>;
  overlayKey: Ref<string>;
}

export function useCanvasLayout(
  props: CanvasLayoutProps,
  appBus: AppEventBus | null
) {
  const flowNodes = ref<Node[]>(mergeLayoutNodes(props.nodes.value, [], false));
  const flowEdges = ref<Edge[]>([]);
  const preserveNodePositions = ref(true);

  function hiddenOverlay(): LayoutEdge[] {
    const f = props.highlight.value;
    if (!f || f.mode !== "node-subtree" || f.hiddenEdgeIds.size === 0) {
      return [];
    }
    return props.hiddenEdges.value.filter((e) => f.hiddenEdgeIds.has(e.id));
  }

  function nodeByIdMap(): Map<string, LayoutNode> {
    return new Map(props.nodes.value.map((n) => [n.id, n]));
  }

  function rebuildFlowEdges() {
    flowEdges.value = buildFlowEdges(
      props.edges.value,
      props.selectedEdgeId.value,
      hiddenOverlay(),
      nodeByIdMap()
    );
    flowNodes.value = applyConnectedHandlesToNodes(flowNodes.value, flowEdges.value);
  }

  rebuildFlowEdges();

  if (appBus) {
    appBus.on("LayoutComputeStarted", (e) => {
      if (e.resetPositions) preserveNodePositions.value = false;
    });
    appBus.on("LayoutRestoredFromHistory", () => {
      preserveNodePositions.value = false;
    });
  }

  watch(
    () => props.nodes.value,
    (layoutNodes) => {
      flowNodes.value = mergeLayoutNodes(
        layoutNodes,
        flowNodes.value,
        preserveNodePositions.value
      );
      flowNodes.value = applyConnectedHandlesToNodes(
        flowNodes.value,
        flowEdges.value
      );
      preserveNodePositions.value = true;
    }
  );

  watch(
    () =>
      [
        props.edges.value,
        props.selectedEdgeId.value,
        props.hiddenEdges.value,
        props.overlayKey.value,
      ] as const,
    rebuildFlowEdges
  );

  function getNodePositions(): Record<string, { x: number; y: number }> {
    return Object.fromEntries(
      flowNodes.value.map((n) => [n.id, { x: n.position.x, y: n.position.y }])
    );
  }

  return {
    flowNodes,
    flowEdges,
    rebuildFlowEdges,
    getNodePositions,
  };
}
