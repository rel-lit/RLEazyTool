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
import { nodeHandleVisibility } from "./nodePorts";
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

const ports = computed(() => nodeHandleVisibility(props.data, dir.value));

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
    <Handle
      v-if="ports['t-l']"
      id="t-l"
      type="target"
      class="fb-handle"
      :position="tL"
    />
    <Handle
      v-if="ports['t-r']"
      id="t-r"
      type="target"
      class="fb-handle"
      :position="tR"
    />
    {{ label }}
    <Handle
      v-if="ports['s-l']"
      id="s-l"
      type="source"
      class="fb-handle"
      :position="sL"
    />
    <Handle
      v-if="ports['s-r']"
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

/* 锚点 invisible：边仍挂接 handle，但不显示圆形连接球 */
.fb-handle {
  opacity: 0 !important;
  width: 1px !important;
  height: 1px !important;
  min-width: 0 !important;
  min-height: 0 !important;
  border: none !important;
  background: transparent !important;
  pointer-events: none !important;
}
</style>
