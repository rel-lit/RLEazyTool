<script setup lang="ts">
import { computed, inject, type Ref } from "vue";
import {
  BaseEdge,
  getBezierPath,
  type EdgeProps,
} from "@vue-flow/core";
import type { LayoutEdge } from "../api/client";
import type { FocusHighlight } from "./focusGraph";
import { isEdgeHighlighted } from "./focusGraph";
import { focusTick } from "./canvasFocus";

export interface BeltEdgeData {
  layoutEdge: LayoutEdge;
  isHiddenOverlay?: boolean;
}

const props = defineProps<EdgeProps<BeltEdgeData>>();

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

const lit = computed(() => {
  focusTick.value;
  if (props.data?.isHiddenOverlay) return true;
  const f = canvasFocus?.value ?? null;
  if (!f) return true;
  return isEdgeHighlighted(props.data!.layoutEdge, f);
});

const mergedStyle = computed(() => ({
  ...(props.style as object),
  opacity: lit.value ? 1 : 0.12,
}));
</script>

<template>
  <BaseEdge
    :id="id"
    :path="pathD"
    :style="mergedStyle"
    :interaction-width="20"
  />
</template>
