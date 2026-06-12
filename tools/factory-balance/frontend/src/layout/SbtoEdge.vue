<script setup lang="ts">
import { computed, inject, type Ref } from "vue";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from "@vue-flow/core";
import type { LayoutEdge } from "../api/client";
import type { FocusHighlight } from "./focusGraph";
import { isEdgeHighlighted, sbtoFlowActive } from "./focusGraph";
import { focusTick } from "./canvasFocus";

export interface SbtoEdgeData {
  layoutEdge: LayoutEdge;
  badgeColor: string;
  tapLabel: string;
}

const props = defineProps<EdgeProps<SbtoEdgeData>>();

const canvasFocus = inject<Ref<FocusHighlight | null>>("canvasFocus");

const bezier = computed(() =>
  getBezierPath({
    sourceX: props.sourceX,
    sourceY: props.sourceY,
    sourcePosition: props.sourcePosition,
    targetX: props.targetX,
    targetY: props.targetY,
    targetPosition: props.targetPosition,
  })
);

const pathD = computed(() => bezier.value[0]);
const labelX = computed(() => bezier.value[1]);
const labelY = computed(() => bezier.value[2]);

const lit = computed(() => {
  focusTick.value;
  const f = canvasFocus?.value ?? null;
  if (!f) return true;
  return isEdgeHighlighted(props.data!.layoutEdge, f);
});

const flowFast = computed(() => {
  focusTick.value;
  const f = canvasFocus?.value ?? null;
  return sbtoFlowActive(props.data!.layoutEdge, f);
});

const mergedStyle = computed(() => ({
  ...(props.style as object),
  opacity: lit.value ? 1 : 0.12,
}));
</script>

<template>
  <g class="sbto-edge" :class="{ 'sbto-edge--fast': flowFast }">
    <BaseEdge
      :id="id"
      :path="pathD"
      :style="mergedStyle"
      :interaction-width="20"
      class="sbto-edge-path"
    />

    <EdgeLabelRenderer v-if="data?.tapLabel">
      <div
        class="sbto-tap-badge"
        :style="{
          transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
          background: data.badgeColor,
          opacity: lit ? 1 : 0.35,
        }"
      >
        {{ data.tapLabel }}
      </div>
    </EdgeLabelRenderer>
  </g>
</template>

<style scoped>
.sbto-edge-path :deep(.vue-flow__edge-path) {
  animation: sbto-dash-flow 6s linear infinite;
}

.sbto-edge--fast .sbto-edge-path :deep(.vue-flow__edge-path) {
  animation-duration: 3s;
}

@keyframes sbto-dash-flow {
  from {
    stroke-dashoffset: 0;
  }
  to {
    stroke-dashoffset: -32;
  }
}

.sbto-tap-badge {
  position: absolute;
  pointer-events: none;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  line-height: 1.2;
}
</style>
