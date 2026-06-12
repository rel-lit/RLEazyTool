<script setup lang="ts">
import { computed, inject, type Ref } from "vue";
import { Handle, Position } from "@vue-flow/core";
import type { LayoutNode } from "../api/client";
import {
  DEFAULT_LAYOUT_DIRECTION,
  type LayoutDirection,
} from "./layoutTypes";
import { factoryNodeClass, factoryNodeLabel } from "./useLayoutFlow";

const props = defineProps<{ data: LayoutNode }>();

const layoutDirection = inject<Ref<LayoutDirection>>(
  "layoutDirection",
  computed(() => DEFAULT_LAYOUT_DIRECTION)
);

const isLr = computed(
  () => (layoutDirection.value ?? DEFAULT_LAYOUT_DIRECTION) === "left-to-right"
);

const sourcePosition = computed(() =>
  isLr.value ? Position.Right : Position.Bottom
);
const targetPosition = computed(() =>
  isLr.value ? Position.Left : Position.Top
);

const label = computed(() => factoryNodeLabel(props.data));
const nodeClass = computed(() => factoryNodeClass(props.data));
</script>

<template>
  <div :class="nodeClass">
    <Handle type="target" :position="targetPosition" />
    {{ label }}
    <Handle type="source" :position="sourcePosition" />
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
