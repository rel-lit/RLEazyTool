<script setup lang="ts">
import { ref } from "vue";

/** 纯展示容器：滚动、边框。不含 commit / focus 逻辑。 */
const rootEl = ref<HTMLElement | null>(null);

defineExpose({ rootEl });
</script>

<template>
  <div ref="rootEl" class="item-list-viewport" @contextmenu.prevent>
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
</style>
