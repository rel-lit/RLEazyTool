<script setup lang="ts">
import { computed, inject, type Ref } from "vue";
import { EdgeLabelRenderer, type EdgeProps } from "@vue-flow/core";
import { bezierPathWithGap } from "./bezierPathWithGap";
import type { LayoutEdge } from "../api/client";
import type { FocusHighlight, FocusPhase } from "./focus";
import { isEdgeHighlighted, sbtoFlowActive } from "./focus";

export interface SbtoEdgeData {
  layoutEdge: LayoutEdge;
  badgeColor: string;
  tapLabel: string;
  fromGrade: number;
  toGrade: number;
  flowSign?: 1 | -1;
  pathGapPx?: number;
  gapNx?: number;
  gapNy?: number;
  pathCurvature?: number;
}

interface CanvasFocusView {
  phase: FocusPhase;
  highlight: FocusHighlight | null;
}

const props = defineProps<EdgeProps<SbtoEdgeData>>();

const focusView = inject<Ref<CanvasFocusView>>("canvasFocusState");

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
const labelX = computed(() => bezier.value[1]);
const labelY = computed(() => bezier.value[2]);

const lit = computed(() => {
  const view = focusView?.value;
  if (!view?.highlight) return true;
  return isEdgeHighlighted(props.data!.layoutEdge, view.highlight);
});

const flowActive = computed(() => {
  const view = focusView?.value;
  if (!view) return false;
  return sbtoFlowActive(
    props.data!.layoutEdge,
    view.phase,
    view.highlight
  );
});

const flowReverse = computed(() => (props.data?.flowSign ?? 1) < 0);

const pathClass = computed(() => {
  const c = ["vue-flow__edge-path", "sbto-dash-path"];
  if (flowActive.value) {
    c.push(flowReverse.value ? "sbto-dash-flow-rev" : "sbto-dash-flow-fwd");
  }
  return c.join(" ");
});

const pathStyle = computed(() => {
  const base = (props.style ?? {}) as Record<string, string | number>;
  return {
    stroke: base.stroke ?? "#b1bac4",
    strokeWidth: base.strokeWidth ?? 2.5,
    strokeDasharray: base.strokeDasharray ?? "10 6",
    fill: "none",
    opacity: lit.value ? 1 : 0.12,
  };
});
</script>

<template>
  <g class="sbto-edge">
    <path
      :d="pathD"
      fill="none"
      stroke="transparent"
      stroke-width="20"
      pointer-events="stroke"
    />
    <path :d="pathD" :class="pathClass" :style="pathStyle" pointer-events="none" />

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

<style>
.sbto-dash-path {
  stroke-linecap: round;
}

.sbto-dash-path.sbto-dash-flow-fwd {
  animation: sbto-dash-flow-fwd 2.5s linear infinite;
}

.sbto-dash-path.sbto-dash-flow-rev {
  animation: sbto-dash-flow-rev 2.5s linear infinite;
}

@keyframes sbto-dash-flow-fwd {
  from {
    stroke-dashoffset: 0;
  }
  to {
    stroke-dashoffset: -32;
  }
}

@keyframes sbto-dash-flow-rev {
  from {
    stroke-dashoffset: 0;
  }
  to {
    stroke-dashoffset: 32;
  }
}
</style>
