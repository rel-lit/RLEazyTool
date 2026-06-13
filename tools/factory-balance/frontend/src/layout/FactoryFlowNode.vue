<script setup lang="ts">
import { computed, inject, type Ref } from "vue";
import { Handle } from "@vue-flow/core";
import type { LayoutNode } from "../api/client";
import type { FocusHighlight } from "./focus";
import { isNodeHighlighted } from "./focus";
import {
  DEFAULT_LAYOUT_DIRECTION,
  type LayoutDirection,
} from "./layoutTypes";
import { factoryNodeLabel, type FactoryNodeData } from "./flowGraph";
import { handlePosition } from "./sbtoPorts";
import type { HandleId } from "./nodePorts";
import { nodeVisualStyle, NODE_BASE_OPACITY } from "./nodeVisual";

const props = defineProps<{ data: FactoryNodeData }>();

const layoutDirection = inject<Ref<LayoutDirection>>(
  "layoutDirection",
  computed(() => DEFAULT_LAYOUT_DIRECTION)
);

const layoutMaxLayer = inject<Ref<number>>(
  "layoutMaxLayer",
  computed(() => 0)
);

const canvasFocus = inject<Ref<FocusHighlight | null>>("canvasFocus");

const dir = computed(
  () => layoutDirection.value ?? DEFAULT_LAYOUT_DIRECTION
);

const connected = computed(
  () => new Set(props.data.connectedHandles ?? [])
);

function showHandle(id: HandleId): boolean {
  return connected.value.has(id);
}

const tL = computed(() => handlePosition("t-l", dir.value));
const tR = computed(() => handlePosition("t-r", dir.value));
const sL = computed(() => handlePosition("s-l", dir.value));
const sR = computed(() => handlePosition("s-r", dir.value));

const dimmed = computed(() => {
  const f = canvasFocus?.value ?? null;
  if (!f) return false;
  return !isNodeHighlighted(props.data.id, f);
});

const label = computed(() => factoryNodeLabel(props.data as LayoutNode));

const nodeStyle = computed(() =>
  nodeVisualStyle(props.data as LayoutNode, layoutMaxLayer.value)
);

const nodeClass = computed(() => [
  "fb-node",
  dimmed.value ? "fb-node--dimmed" : "",
]);
</script>

<template>
  <div :class="nodeClass" :style="nodeStyle">
    <Handle
      v-if="showHandle('t-l')"
      id="t-l"
      type="target"
      class="fb-handle"
      :position="tL"
    />
    <Handle
      v-if="showHandle('t-r')"
      id="t-r"
      type="target"
      class="fb-handle"
      :position="tR"
    />
    {{ label }}
    <Handle
      v-if="showHandle('s-l')"
      id="s-l"
      type="source"
      class="fb-handle"
      :position="sL"
    />
    <Handle
      v-if="showHandle('s-r')"
      id="s-r"
      type="source"
      class="fb-handle"
      :position="sR"
    />
  </div>
</template>

<style scoped>
.fb-node {
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
  min-width: 100px;
  text-align: center;
  color: #fff;
  opacity: v-bind("NODE_BASE_OPACITY");
  background: var(--fb-bg);
  border: var(--fb-border-width, 1px) var(--fb-border-style, solid)
    var(--fb-border, #484f58);
  transition: opacity 0.12s ease, filter 0.12s ease;
}

.fb-node--dimmed {
  opacity: 0.12 !important;
  filter: grayscale(0.55);
}

.fb-handle {
  width: 8px;
  height: 8px;
  background: #9aa4af;
  border: 2px solid #30363d;
}
</style>
