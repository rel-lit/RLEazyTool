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
    selectedTargets: string[];
    /** 由编排层注入；缺省不显示关联标记 */
    resolveLayoutMark?: (itemName: string) => ListLayoutMark;
  }>(),
  {
    resolveLayoutMark: () => () => LIST_LAYOUT_MARK_NONE,
  }
);

defineEmits<{
  toggleTarget: [name: string];
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
    <div class="chip-list">
      <UiChip
        v-for="item in visibleItems"
        :key="item.name"
        :selected="selectedTargets.includes(item.name)"
        :layout-mark="layoutMarkFor(item.name)"
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
