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
import { factoryNodeLabel } from "./flowGraph";
import { handlePosition } from "./sbtoPorts";
import { nodeVisualStyle, NODE_BASE_OPACITY } from "./nodeVisual";

const props = defineProps<{ data: LayoutNode }>();

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

const tL = computed(() => handlePosition("t-l", dir.value));
const tR = computed(() => handlePosition("t-r", dir.value));
const sL = computed(() => handlePosition("s-l", dir.value));
const sR = computed(() => handlePosition("s-r", dir.value));

const dimmed = computed(() => {
  const f = canvasFocus?.value ?? null;
  if (!f) return false;
  return !isNodeHighlighted(props.data.id, f);
});

const label = computed(() => factoryNodeLabel(props.data));

const nodeStyle = computed(() => nodeVisualStyle(props.data, layoutMaxLayer.value));

const nodeClass = computed(() => [
  "fb-node",
  dimmed.value ? "fb-node--dimmed" : "",
]);
</script>

<template>
  <div :class="nodeClass" :style="nodeStyle">
    <Handle id="t-l" type="target" :position="tL" />
    <Handle id="t-r" type="target" :position="tR" />
    {{ label }}
    <Handle id="s-l" type="source" :position="sL" />
    <Handle id="s-r" type="source" :position="sR" />
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
</style>
