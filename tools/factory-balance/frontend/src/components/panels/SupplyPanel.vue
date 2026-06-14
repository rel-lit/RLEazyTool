<script setup lang="ts">
import { computed } from "vue";
import type { ItemInfo } from "../../api/client";
import type { ListLayoutMark } from "../../domains/list-layout-mark";
import { LIST_LAYOUT_MARK_NONE } from "../../domains/list-layout-mark";
import { applyListMask } from "../../domains/item-list";
import { UiChip } from "../../ui";

const props = withDefaults(
  defineProps<{
    displayOrder: ItemInfo[];
    searchQuery: string;
    suppliedItems: string[];
    forbiddenItems: string[];
    resolveLayoutMark?: (itemName: string) => ListLayoutMark;
  }>(),
  {
    resolveLayoutMark: () => () => LIST_LAYOUT_MARK_NONE,
  }
);

defineEmits<{
  toggleSupplied: [name: string];
  toggleForbidden: [name: string];
}>();

const visibleItems = computed(() => applyListMask(props.displayOrder, props.searchQuery));

function layoutMarkFor(name: string): ListLayoutMark {
  try {
    return props.resolveLayoutMark(name);
  } catch {
    return LIST_LAYOUT_MARK_NONE;
  }
}
</script>

<template>
  <section>
    <p class="hint">左键：已知供给 · 右键：禁止供给</p>
    <div class="chip-list">
      <UiChip
        v-for="item in visibleItems"
        :key="'s-' + item.name"
        size="sm"
        :selected="suppliedItems.includes(item.name)"
        :forbidden="forbiddenItems.includes(item.name)"
        :layout-mark="layoutMarkFor(item.name)"
        @primary="$emit('toggleSupplied', item.name)"
        @secondary="$emit('toggleForbidden', item.name)"
      >
        {{ item.label }}
      </UiChip>
    </div>
  </section>
</template>

<style scoped>
.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.hint {
  font-size: 12px;
  color: #8b949e;
  margin: 0 0 8px;
}
</style>
