<script setup lang="ts">
import { computed, inject, onMounted, onUnmounted, provide, ref, toRef } from "vue";
import { VueFlow } from "@vue-flow/core";
import type { LayoutEdge, LayoutNode } from "../api/client";
import { canvasLayoutHooksKey, layoutInspectionKey } from "../app/useApp";
import { Background } from "@vue-flow/background";
import "@vue-flow/core/dist/style.css";
import "@vue-flow/core/dist/theme-default.css";
import FactoryFlowNode from "../layout/FactoryFlowNode.vue";
import BeltEdge from "../layout/BeltEdge.vue";
import SbtoEdge from "../layout/SbtoEdge.vue";
import {
  focusDebugLog,
  isFocusDebugEnabled,
} from "../layout/focusDebug";
import { useLayoutCanvasRegion } from "../layout/useLayoutCanvasRegion";
import { useCanvasLayout } from "../layout/useCanvasLayout";
import {
  registerCanvasPositionReader,
  unregisterCanvasPositionReader,
} from "../layout/layoutCanvasBridge";
import {
  DEFAULT_LAYOUT_DIRECTION,
  type LayoutDirection,
} from "../layout/layoutTypes";
import { layoutMaxLayer } from "../layout/nodeVisual";

const props = defineProps<{
  nodes: LayoutNode[];
  edges: LayoutEdge[];
  productEdges: LayoutEdge[];
  hiddenEdges: LayoutEdge[];
  layoutDirection?: LayoutDirection;
}>();

const canvasHooks = inject(canvasLayoutHooksKey)!;
const inspection = inject(layoutInspectionKey)!;

const direction = computed(
  () => props.layoutDirection ?? DEFAULT_LAYOUT_DIRECTION
);
provide("layoutDirection", direction);

const maxLayer = computed(() => layoutMaxLayer(props.nodes));
provide("layoutMaxLayer", maxLayer);

const region = useLayoutCanvasRegion({
  ctx: {
    nodes: toRef(props, "nodes"),
    edges: toRef(props, "edges"),
    productEdges: toRef(props, "productEdges"),
    hiddenEdges: toRef(props, "hiddenEdges"),
  },
  pin: inspection.pin,
  onPrimary: (target) => inspection.handlePrimary(target),
});

provide(
  "canvasFocusState",
  computed(() => ({
    phase: region.phase.value,
    highlight: region.highlight.value,
  }))
);
provide("canvasFocus", region.highlight);

const canvasLayout = useCanvasLayout({
  nodes: toRef(props, "nodes"),
  edges: toRef(props, "edges"),
  hiddenEdges: toRef(props, "hiddenEdges"),
  selectedEdgeId: inspection.selectedEdgeId,
  highlight: region.highlight,
  overlayKey: region.overlayKey,
});

const { flowNodes, flowEdges, rebuildFlowEdges, getNodePositions, prepareForNewLayout } =
  canvasLayout;
const { handlers } = region;

const debugOn = ref(false);
const debugLastEvent = ref("—");

onMounted(() => {
  debugOn.value = isFocusDebugEnabled();
  registerCanvasPositionReader(getNodePositions);
  canvasHooks.prepareForNewLayout = prepareForNewLayout;
});

onUnmounted(() => {
  unregisterCanvasPositionReader();
});

defineExpose({ getNodePositions });

const nodeTypes = { factory: FactoryFlowNode };
const edgeTypes = { sbto: SbtoEdge, belt: BeltEdge };

function onNodeEnter({ node }: { node: { id: string } }) {
  focusDebugLog({ kind: "node-enter", id: node.id });
  debugLastEvent.value = `节点 ${node.id}`;
  handlers.onNodeEnter(node.id);
}

function onNodeLeave() {
  focusDebugLog({ kind: "node-leave" });
  debugLastEvent.value = "node-leave";
  handlers.onNodeLeave();
}

function onEdgeEnter({ edge }: { edge: { id: string } }) {
  focusDebugLog({ kind: "edge-enter", id: edge.id });
  debugLastEvent.value = `边 ${edge.id}`;
  handlers.onEdgeEnter(edge.id);
}

function onEdgeLeave() {
  focusDebugLog({ kind: "edge-leave" });
  debugLastEvent.value = "edge-leave";
  handlers.onEdgeLeave();
}

function onNodeClick({ node }: { node: { id: string } }) {
  handlers.onNodeClick(node.id);
}

function onEdgeClick({ edge }: { edge: { id: string } }) {
  handlers.onEdgeClick(edge.id);
}

function onPaneClick() {
  handlers.onPaneClick();
}

function onDragStart() {
  handlers.onDragStart();
  rebuildFlowEdges();
}

function onDragStop() {
  handlers.onDragStop();
}

function debugSummary(): string {
  const pin = region.isPinned.value ? " [pinned]" : "";
  const h = region.highlight.value;
  if (!h) return "—" + pin;
  return `${h.mode}${pin}`;
}
</script>

<template>
  <div class="canvas-root">
    <div v-if="debugOn" class="focus-debug-hud">
      <div><strong>Focus 调试</strong>（localStorage fb-debug-focus=1）</div>
      <div>事件: {{ debugLastEvent }}</div>
      <div>相态: {{ region.phase }}</div>
      <div>高亮: {{ debugSummary() }}</div>
    </div>
    <VueFlow
      v-model:nodes="flowNodes"
      :edges="flowEdges"
      :node-types="nodeTypes"
      :edge-types="edgeTypes"
      :nodes-connectable="false"
      fit-view-on-init
      @edge-click="onEdgeClick"
      @node-click="onNodeClick"
      @node-mouse-enter="onNodeEnter"
      @node-mouse-leave="onNodeLeave"
      @edge-mouse-enter="onEdgeEnter"
      @edge-mouse-leave="onEdgeLeave"
      @node-drag-start="onDragStart"
      @node-drag-stop="onDragStop"
      @pane-click="onPaneClick"
    >
      <Background pattern-color="#30363d" :gap="16" />
    </VueFlow>
  </div>
</template>

<style scoped>
.canvas-root {
  width: 100%;
  height: 100%;
  position: relative;
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
  transition: opacity 0.12s ease;
}

:deep(.vue-flow__node-default) {
  background: transparent;
  border: none;
  padding: 0;
  box-shadow: none;
}

.focus-debug-hud {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 10;
  padding: 8px 10px;
  border-radius: 6px;
  background: rgba(13, 17, 23, 0.92);
  border: 1px solid #30363d;
  color: #8b949e;
  font-size: 11px;
  line-height: 1.45;
  pointer-events: none;
  max-width: 280px;
}
</style>
