<script setup lang="ts">
import { computed, inject } from "vue";
import type { ItemInfo } from "../../api/client";
import { listLayoutMarkKey } from "../../app/useApp";
import { applyListMask } from "../../domains/item-list";
import { UiChip } from "../../ui";

const props = defineProps<{
  displayOrder: ItemInfo[];
  searchQuery: string;
  suppliedItems: string[];
  forbiddenItems: string[];
}>();

defineEmits<{
  toggleSupplied: [name: string];
  toggleForbidden: [name: string];
}>();

const listLayoutMark = inject(listLayoutMarkKey)!;

const visibleItems = computed(() => applyListMask(props.displayOrder, props.searchQuery));

const markRevision = computed(() => listLayoutMark.revision.value);

function layoutMarkFor(name: string) {
  void markRevision.value;
  return listLayoutMark.getListLayoutMark(name, "supply");
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
        :layout-mark="layoutMarkFor(item.name).kind"
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
