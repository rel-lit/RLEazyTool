<script setup lang="ts">
import { computed } from "vue";
import type { LayoutEdge, LayoutNode } from "../api/client";
import { Background } from "@vue-flow/background";
import { VueFlow, type Edge, type Node } from "@vue-flow/core";
import "@vue-flow/core/dist/style.css";
import "@vue-flow/core/dist/theme-default.css";

const props = defineProps<{
  nodes: LayoutNode[];
  edges: LayoutEdge[];
  selectedEdgeId: string | null;
}>();

const emit = defineEmits<{ selectEdge: [id: string | null] }>();

const vfNodes = computed<Node[]>(() =>
  props.nodes.map((n) => ({
    id: n.id,
    type: "default",
    position: { x: n.position.x, y: n.position.y },
    label: n.label,
    data: n,
    style: nodeStyle(n),
  }))
);

const vfEdges = computed<Edge[]>(() =>
  props.edges.map((e) => ({
    id: e.id,
    source: e.from,
    target: e.to,
    label: edgeLabel(e),
    animated: e.self_balance,
    style: edgeStyle(e, props.selectedEdgeId === e.id),
  }))
);

function nodeStyle(n: LayoutNode): Record<string, string> {
  const colors: Record<string, string> = {
    supply: "#238636",
    producer: "#1f6feb",
    sink: "#8957e5",
    buffer_placeholder: "#6e7681",
  };
  return {
    background: colors[n.type] ?? "#30363d",
    color: "#fff",
    border: "1px solid #484f58",
    borderRadius: "8px",
    padding: "8px 12px",
    fontSize: "13px",
    minWidth: "100px",
    textAlign: "center",
  };
}

function edgeStyle(e: LayoutEdge, selected: boolean): Record<string, string | number> {
  const base: Record<string, string | number> = {
    stroke: e.type === "detour" ? "#f0883e" : e.self_balance ? "#58a6ff" : "#8b949e",
    strokeWidth: selected ? 3 : 2,
  };
  if (e.type === "detour") {
    base.strokeDasharray = "6 4";
  }
  return base;
}

function edgeLabel(e: LayoutEdge): string {
  const tap = e.tap_index ? ` ①②③`.charAt(Math.min(e.tap_index - 1, 2)) || `#${e.tap_index}` : "";
  return `${e.label}${e.tap_index ? ` (${e.tap_index})` : ""}`;
}
</script>

<template>
  <div class="canvas-root">
    <VueFlow
      :nodes="vfNodes"
      :edges="vfEdges"
      fit-view-on-init
      @edge-click="({ edge }) => emit('selectEdge', edge.id)"
      @pane-click="emit('selectEdge', null)"
    >
      <Background pattern-color="#30363d" :gap="16" />
    </VueFlow>
  </div>
</template>

<style scoped>
.canvas-root {
  width: 100%;
  height: 100%;
}

:deep(.vue-flow) {
  width: 100%;
  height: 100%;
  background: #161b22;
}

:deep(.vue-flow__viewport) {
  width: 100%;
  height: 100%;
}
</style>
