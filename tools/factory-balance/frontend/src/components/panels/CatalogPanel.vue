<script setup lang="ts">
import { computed } from "vue";
import type { ItemInfo } from "../../api/client";
import { resolveItemIconUrl } from "../../api/iconUrl";
import type { ListLayoutMark } from "../../domains/list-layout-mark";
import { LIST_LAYOUT_MARK_NONE } from "../../domains/list-layout-mark";
import { applyListMask } from "../../domains/item-list";
import { UiChip } from "../../ui";
import ListChipShell from "../item-list/ListChipShell.vue";

const props = withDefaults(
  defineProps<{
    displayOrder: ItemInfo[];
    searchQuery: string;
    selectedTargets: string[];
    /** 由编排层注入；缺省不显示关联标记 */
    resolveLayoutMark?: (itemName: string) => ListLayoutMark;
    /** 画布钉选子树：列表额外圈选（layout-inspection，与 layout-mark 无关） */
    canvasFocusRing?: (itemName: string) => boolean;
  }>(),
  {
    resolveLayoutMark: () => () => LIST_LAYOUT_MARK_NONE,
    canvasFocusRing: () => () => false,
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
      <ListChipShell
        v-for="item in visibleItems"
        :key="item.name"
        :canvas-focus="canvasFocusRing(item.name)"
      >
        <UiChip
          size="sm"
          :selected="selectedTargets.includes(item.name)"
          :layout-mark="layoutMarkFor(item.name)"
          :icon-url="resolveItemIconUrl(item.icon_slug)"
          @primary="$emit('toggleTarget', item.name)"
        >
          {{ item.label }}
          <span v-if="item.expansion === 'space-age'" class="tag">SA</span>
        </UiChip>
      </ListChipShell>
    </div>
  </section>
</template>

<style scoped>
.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 4px;
  overflow: visible;
}

.tag {
  margin-left: 4px;
  font-size: 10px;
  opacity: 0.85;
}
</style>
