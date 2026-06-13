<script setup lang="ts">
import { ref } from "vue";
import { useScrollRegion } from "../../ui/interaction";

const rootEl = ref<HTMLElement | null>(null);

const { resetScroll } = useScrollRegion(rootEl);

defineExpose({ rootEl, resetScroll });
</script>

<template>
  <div ref="rootEl" class="item-list-viewport" tabindex="-1">
    <slot />
  </div>
</template>

<style scoped>
.item-list-viewport {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px;
  margin-top: 2px;
  border: 1px solid var(--ui-border, #30363d);
  border-radius: var(--ui-radius, 6px);
  background: var(--ui-bg-inset, #0d1117);
}

.item-list-viewport:focus {
  outline: none;
}
</style>
