<script setup lang="ts">
/** 列表 chip 外框：画布钉选圈选（layout-inspection）与 chip 本体解耦 */
defineProps<{
  canvasFocus?: boolean;
}>();
</script>

<template>
  <span
    class="list-chip-shell"
    :class="{ 'list-chip-shell--canvas-focus': canvasFocus }"
  >
    <slot />
    <svg
      v-if="canvasFocus"
      class="list-chip-shell__focus-ring"
      viewBox="0 0 100 24"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <rect
        class="list-chip-shell__focus-stroke"
        x="1.25"
        y="1.25"
        width="97.5"
        height="21.5"
        rx="10.75"
        ry="10.75"
        pathLength="240"
      />
    </svg>
  </span>
</template>

<style scoped>
.list-chip-shell {
  position: relative;
  display: inline-flex;
  max-width: 100%;
  vertical-align: top;
}

.list-chip-shell__focus-ring {
  position: absolute;
  inset: -3px;
  width: calc(100% + 6px);
  height: calc(100% + 6px);
  overflow: visible;
  pointer-events: none;
  z-index: 0;
}

.list-chip-shell__focus-stroke {
  fill: none;
  stroke: hsla(140, 55%, 58%, 0.88);
  stroke-width: 1.75;
  stroke-dasharray: 7 5;
  stroke-linecap: round;
  vector-effect: non-scaling-stroke;
  animation: list-chip-focus-march 2.5s linear infinite;
}

@keyframes list-chip-focus-march {
  from {
    stroke-dashoffset: 0;
  }
  to {
    stroke-dashoffset: -24;
  }
}

.list-chip-shell--canvas-focus :deep(.ui-chip) {
  position: relative;
  z-index: 1;
}
</style>
