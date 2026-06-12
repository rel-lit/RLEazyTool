<script setup lang="ts">
import { computed, provide, toRef } from "vue";
import type { LayoutEdge, LayoutNode } from "../api/client";
import { Background } from "@vue-flow/background";
import { VueFlow } from "@vue-flow/core";
import "@vue-flow/core/dist/style.css";
import "@vue-flow/core/dist/theme-default.css";
import FactoryFlowNode from "../layout/FactoryFlowNode.vue";
import {
  DEFAULT_LAYOUT_DIRECTION,
  type LayoutDirection,
} from "../layout/layoutTypes";
import { useLayoutFlow } from "../layout/useLayoutFlow";

const props = defineProps<{
  nodes: LayoutNode[];
  edges: LayoutEdge[];
  selectedEdgeId: string | null;
  layoutDirection?: LayoutDirection;
}>();

const emit = defineEmits<{ selectEdge: [id: string | null] }>();

const direction = computed(
  () => props.layoutDirection ?? DEFAULT_LAYOUT_DIRECTION
);
provide("layoutDirection", direction);

const { vfNodes, vfEdges } = useLayoutFlow(
  toRef(props, "nodes"),
  toRef(props, "edges"),
  direction,
  toRef(props, "selectedEdgeId")
);

const nodeTypes = { factory: FactoryFlowNode };
</script>

<template>
  <div class="canvas-root">
    <VueFlow
      :nodes="vfNodes"
      :edges="vfEdges"
      :node-types="nodeTypes"
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

:deep(.vue-flow__edge-path) {
  stroke-linecap: round;
}

:deep(.vue-flow__node-default) {
  background: transparent;
  border: none;
  padding: 0;
  box-shadow: none;
}
</style>
