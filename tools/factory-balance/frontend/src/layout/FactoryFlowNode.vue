<script setup lang="ts">
import { computed, inject, type Ref } from "vue";
import { Handle } from "@vue-flow/core";
import type { LayoutNode } from "../api/client";
import type { FocusHighlight } from "./focusGraph";
import { isNodeHighlighted } from "./focusGraph";
import {
  DEFAULT_LAYOUT_DIRECTION,
  type LayoutDirection,
} from "./layoutTypes";
import { factoryNodeClass, factoryNodeLabel } from "./flowGraph";
import { focusTick } from "./canvasFocus";
import { handlePosition } from "./sbtoPorts";

const props = defineProps<{ data: LayoutNode }>();

const layoutDirection = inject<Ref<LayoutDirection>>(
  "layoutDirection",
  computed(() => DEFAULT_LAYOUT_DIRECTION)
);

const canvasFocus = inject<Ref<FocusHighlight | null>>("canvasFocus");
const enterFocusFromNode = inject<
  (nodeId: string, source: string) => void
>("enterFocusFromNode");
const scheduleClearFocus = inject<() => void>("scheduleClearFocus");

const dir = computed(
  () => layoutDirection.value ?? DEFAULT_LAYOUT_DIRECTION
);

const tL = computed(() => handlePosition("t-l", dir.value));
const tR = computed(() => handlePosition("t-r", dir.value));
const sL = computed(() => handlePosition("s-l", dir.value));
const sR = computed(() => handlePosition("s-r", dir.value));

const dimmed = computed(() => {
  focusTick.value;
  const f = canvasFocus?.value ?? null;
  if (!f) return false;
  return !isNodeHighlighted(props.data.id, f);
});

const label = computed(() => factoryNodeLabel(props.data));
const nodeClass = computed(() => [
  factoryNodeClass(props.data),
  dimmed.value ? "fb-node--dimmed" : "",
]);

function onNodeMouseEnter() {
  enterFocusFromNode?.(props.data.id, `节点内 ${props.data.id}`);
}

function onNodeMouseLeave() {
  scheduleClearFocus?.();
}
</script>

<template>
  <div
    :class="nodeClass"
    @mouseenter="onNodeMouseEnter"
    @mouseleave="onNodeMouseLeave"
  >
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
  transition: opacity 0.12s ease, filter 0.12s ease;
}

.fb-node--dimmed {
  opacity: 0.12;
  filter: grayscale(0.55);
}

.fb-node--supply {
  background: #238636;
  border: 1px solid #484f58;
}

.fb-node--supply.fb-node--world-baseline {
  background: #1a4d2e;
  border: 2px solid #3fb950;
}

.fb-node--producer {
  background: #1f6feb;
  border: 1px solid #484f58;
}

.fb-node--producer.fb-node--world-extract {
  background: #1f3d5c;
  border: 2px dashed #58a6ff;
}

.fb-node--sink {
  background: #8957e5;
  border: 1px solid #484f58;
}

.fb-node--buffer_placeholder {
  background: #6e7681;
  border: 1px solid #484f58;
}
</style>
