<script setup lang="ts">
import { computed, inject } from "vue";
import type { ItemInfo } from "../../api/client";
import { listLayoutMarkKey } from "../../app/useApp";
import { applyListMask } from "../../domains/item-list";
import { UiChip } from "../../ui";

const props = defineProps<{
  displayOrder: ItemInfo[];
  searchQuery: string;
  selectedTargets: string[];
}>();

defineEmits<{
  toggleTarget: [name: string];
}>();

const listLayoutMark = inject(listLayoutMarkKey)!;

const visibleItems = computed(() => applyListMask(props.displayOrder, props.searchQuery));

const markRevision = computed(() => listLayoutMark.revision.value);

function layoutMarkFor(name: string) {
  void markRevision.value;
  return listLayoutMark.getListLayoutMark(name);
}
</script>

<template>
  <section>
    <div class="chip-list">
      <UiChip
        v-for="item in visibleItems"
        :key="item.name"
        :selected="selectedTargets.includes(item.name)"
        :layout-mark="layoutMarkFor(item.name).kind"
        @primary="$emit('toggleTarget', item.name)"
      >
        {{ item.label }}
        <span v-if="item.expansion === 'space-age'" class="tag">SA</span>
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

.tag {
  margin-left: 4px;
  font-size: 10px;
  opacity: 0.85;
}
</style>
