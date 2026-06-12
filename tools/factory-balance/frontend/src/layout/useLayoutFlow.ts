import { computed, type ComputedRef, type Ref } from "vue";
import type { Edge, Node } from "@vue-flow/core";
import type { LayoutEdge, LayoutNode } from "../api/client";
import {
  DEFAULT_LAYOUT_DIRECTION,
  type LayoutDirection,
} from "./layoutTypes";

export function flowPorts(direction: LayoutDirection): {
  source: "right" | "bottom";
  target: "left" | "top";
} {
  if (direction === "left-to-right") {
    return { source: "right", target: "left" };
  }
  return { source: "bottom", target: "top" };
}

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

function edgeStyle(
  e: LayoutEdge,
  selected: boolean
): Record<string, string | number> {
  const base: Record<string, string | number> = {
    stroke:
      e.type === "detour"
        ? "#f0883e"
        : e.type === "tap_chain"
          ? "#58a6ff"
          : "#8b949e",
    strokeWidth: selected ? 3 : 2,
  };
  if (e.type === "detour") {
    base.strokeDasharray = "6 4";
  }
  return base;
}

function edgeLabel(e: LayoutEdge): string {
  return e.tap_index != null ? String(e.tap_index) : "";
}

export function useLayoutFlow(
  nodes: Ref<LayoutNode[]> | ComputedRef<LayoutNode[]>,
  edges: Ref<LayoutEdge[]> | ComputedRef<LayoutEdge[]>,
  layoutDirection: Ref<LayoutDirection> | ComputedRef<LayoutDirection>,
  selectedEdgeId: Ref<string | null> | ComputedRef<string | null>
) {
  const direction = computed(
    () => layoutDirection.value ?? DEFAULT_LAYOUT_DIRECTION
  );

  const vfNodes = computed<Node[]>(() =>
    nodes.value.map((n) => ({
      id: n.id,
      type: "factory",
      position: { x: n.position.x, y: n.position.y },
      data: n,
    }))
  );

  const vfEdges = computed<Edge[]>(() =>
    edges.value.map((e) => ({
      id: e.id,
      source: e.from,
      target: e.to,
      label: edgeLabel(e),
      animated: e.type === "tap_chain" || e.self_balance === true,
      style: edgeStyle(e, selectedEdgeId.value === e.id),
    }))
  );

  return { vfNodes, vfEdges, direction };
}
