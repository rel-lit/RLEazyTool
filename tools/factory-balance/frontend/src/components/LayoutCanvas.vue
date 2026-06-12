<script setup lang="ts">
/**
 * 画布架构（三层分离）：
 * 1. layout props → flowNodes/flowEdges（仅布局重算 + 用户拖动）
 * 2. canvasFocus ref → 悬停高亮逻辑（focusGraph）
 * 3. focus 视觉 → provide + 组件 inject + paintFocusVisual(DOM)，绝不写回 nodes
 */
import { VueFlow } from "@vue-flow/core";
import { computed, nextTick, onMounted, provide, ref, watch } from "vue";
import type { LayoutEdge, LayoutNode } from "../api/client";
import { Background } from "@vue-flow/background";
import "@vue-flow/core/dist/style.css";
import "@vue-flow/core/dist/theme-default.css";
import FactoryFlowNode from "../layout/FactoryFlowNode.vue";
import {
  focusFromEdge,
  focusFromNode,
  type FocusHighlight,
} from "../layout/focusGraph";
import { bumpFocusTick } from "../layout/canvasFocus";
import BeltEdge from "../layout/BeltEdge.vue";
import {
  focusDebugLog,
  focusDebugSummary,
  isFocusDebugEnabled,
} from "../layout/focusDebug";
import { paintFocusVisual } from "../layout/focusVisual";
import { buildFlowEdges, mergeLayoutNodes } from "../layout/flowGraph";
import {
  DEFAULT_LAYOUT_DIRECTION,
  type LayoutDirection,
} from "../layout/layoutTypes";
import SbtoEdge from "../layout/SbtoEdge.vue";

const props = defineProps<{
  nodes: LayoutNode[];
  edges: LayoutEdge[];
  productEdges: LayoutEdge[];
  hiddenEdges: LayoutEdge[];
  selectedEdgeId: string | null;
  layoutDirection?: LayoutDirection;
}>();

const emit = defineEmits<{ selectEdge: [id: string | null] }>();

const direction = computed(
  () => props.layoutDirection ?? DEFAULT_LAYOUT_DIRECTION
);
provide("layoutDirection", direction);

const canvasRoot = ref<HTMLElement | null>(null);
const focus = ref<FocusHighlight | null>(null);
const isDragging = ref(false);
const debugOn = ref(false);
const debugLastEvent = ref("—");
const debugFocusSummary = ref("无高亮");
provide("canvasFocus", focus);

function applyFocus(next: FocusHighlight | null, source: string) {
  if (isDragging.value) return;
  focus.value = next;
  debugLastEvent.value = source;
  debugFocusSummary.value = focusDebugSummary(next);
  focusDebugLog({ kind: "focus", focus: next });
}

function enterFocusFromNode(nodeId: string, source: string) {
  if (isDragging.value) return;
  cancelClearFocus();
  applyFocus(
    focusFromNode(
      nodeId,
      props.productEdges,
      props.hiddenEdges,
      props.edges,
      props.nodes
    ),
    source
  );
}

function enterFocusFromEdge(edgeId: string, source: string) {
  if (isDragging.value) return;
  cancelClearFocus();
  const le = layoutEdge(edgeId);
  if (le) {
    applyFocus(focusFromEdge(le, props.edges), source);
  }
}

provide("enterFocusFromNode", enterFocusFromNode);

const flowNodes = ref(mergeLayoutNodes(props.nodes, []));
const flowEdges = ref(buildDisplayEdges());

function hiddenOverlay(): LayoutEdge[] {
  const f = focus.value;
  if (f?.mode !== "node-subtree" || f.hiddenEdgeIds.size === 0) {
    return [];
  }
  return props.hiddenEdges.filter((e) => f.hiddenEdgeIds.has(e.id));
}

function buildDisplayEdges() {
  return buildFlowEdges(
    props.edges,
    props.selectedEdgeId,
    hiddenOverlay()
  );
}

let focusClearTimer: ReturnType<typeof setTimeout> | null = null;

function cancelClearFocus() {
  if (focusClearTimer) {
    clearTimeout(focusClearTimer);
    focusClearTimer = null;
  }
}

function scheduleClearFocus() {
  cancelClearFocus();
  focusClearTimer = setTimeout(() => {
    focus.value = null;
    debugFocusSummary.value = focusDebugSummary(null);
    focusDebugLog({ kind: "focus", focus: null });
    focusClearTimer = null;
  }, 120);
}

provide("scheduleClearFocus", scheduleClearFocus);

function clearFocus() {
  cancelClearFocus();
  focus.value = null;
}

const nodeTypes = { factory: FactoryFlowNode };
const edgeTypes = { sbto: SbtoEdge, belt: BeltEdge };

onMounted(() => {
  debugOn.value = isFocusDebugEnabled();
});

/** 布局 API 结果变化：合并坐标，不碰 focus */
watch(
  () => props.nodes,
  (layoutNodes) => {
    flowNodes.value = mergeLayoutNodes(layoutNodes, flowNodes.value);
    if (focus.value && !isDragging.value) {
      repaintFocus();
    }
  }
);

watch(
  () => [props.edges, props.selectedEdgeId, props.hiddenEdges] as const,
  () => {
    flowEdges.value = buildDisplayEdges();
  }
);

/** focus 变化：临时 overlay hidden 边 + 绘制虚化 */
watch(focus, (f) => {
  if (isDragging.value) return;
  flowEdges.value = buildDisplayEdges();
  bumpFocusTick();
  repaintFocus();
});

function layoutEdge(id: string): LayoutEdge | undefined {
  return props.edges.find((e) => e.id === id);
}

function repaintFocus() {
  nextTick(() => {
    requestAnimationFrame(() => {
      paintFocusVisual(canvasRoot.value, focus.value);
    });
  });
}

function onNodeEnter({ node }: { node: { id: string } }) {
  focusDebugLog({ kind: "node-enter", id: node.id });
  enterFocusFromNode(node.id, `节点 ${node.id}`);
}

function onNodeLeave() {
  if (isDragging.value) return;
  focusDebugLog({ kind: "node-leave" });
  scheduleClearFocus();
}

function onEdgeEnter({ edge }: { edge: { id: string } }) {
  focusDebugLog({ kind: "edge-enter", id: edge.id });
  enterFocusFromEdge(edge.id, `边 ${edge.id}`);
}

function onEdgeLeave() {
  if (isDragging.value) return;
  focusDebugLog({ kind: "edge-leave" });
  scheduleClearFocus();
}

function onNodeDragStart() {
  isDragging.value = true;
  cancelClearFocus();
  focus.value = null;
  bumpFocusTick();
  repaintFocus();
}

function onNodeDragStop() {
  isDragging.value = false;
}
</script>

<template>
  <div ref="canvasRoot" class="canvas-root">
    <div v-if="debugOn" class="focus-debug-hud">
      <div><strong>Focus 调试</strong>（localStorage fb-debug-focus=1）</div>
      <div>事件: {{ debugLastEvent }}</div>
      <div>高亮: {{ debugFocusSummary }}</div>
    </div>
    <VueFlow
      v-model:nodes="flowNodes"
      v-model:edges="flowEdges"
      :node-types="nodeTypes"
      :edge-types="edgeTypes"
      :nodes-connectable="false"
      fit-view-on-init
      @edge-click="({ edge }) => emit('selectEdge', edge.id)"
      @node-mouse-enter="onNodeEnter"
      @node-mouse-leave="onNodeLeave"
      @edge-mouse-enter="onEdgeEnter"
      @edge-mouse-leave="onEdgeLeave"
      @node-drag-start="onNodeDragStart"
      @node-drag-stop="onNodeDragStop"
      @pane-click="
        emit('selectEdge', null);
        clearFocus();
      "
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

:deep(.vue-flow__node) {
  transition: opacity 0.12s ease, filter 0.12s ease;
}

/* DOM 绘制备用：包裹层虚化 */
:deep(.vue-flow__node.vf-dim) {
  opacity: 0.12 !important;
  filter: grayscale(0.55) !important;
}

:deep(.vue-flow__edge.vf-dim .vue-flow__edge-path) {
  opacity: 0.12 !important;
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
