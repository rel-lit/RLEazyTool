<script setup lang="ts">
import { computed, inject, type Ref } from "vue";
import { BaseEdge, type EdgeProps } from "@vue-flow/core";
import { bezierPathWithGap } from "./bezierPathWithGap";
import type { LayoutEdge } from "../api/client";
import type { FocusHighlight } from "./focus";
import { isEdgeHighlighted } from "./focus";

export interface BeltEdgeData {
  layoutEdge: LayoutEdge;
  isHiddenOverlay?: boolean;
  pathGapPx?: number;
  gapNx?: number;
  gapNy?: number;
  pathCurvature?: number;
}

const props = defineProps<EdgeProps<BeltEdgeData>>();

const canvasFocus = inject<Ref<FocusHighlight | null>>("canvasFocus");

const bezier = computed(() => {
  const gap = props.data?.pathGapPx ?? 0;
  const [path, lx, ly] = bezierPathWithGap({
    sourceX: props.sourceX,
    sourceY: props.sourceY,
    sourcePosition: props.sourcePosition,
    targetX: props.targetX,
    targetY: props.targetY,
    targetPosition: props.targetPosition,
    curvature: props.data?.pathCurvature ?? 0.25,
    gapPx: gap,
    gapNx: props.data?.gapNx,
    gapNy: props.data?.gapNy,
  });
  return [path, lx, ly] as const;
});

const pathD = computed(() => bezier.value[0]);

const lit = computed(() => {
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
