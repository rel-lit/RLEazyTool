<script setup lang="ts">
import type { ItemInfo } from "../../api/client";
import { UiChip } from "../../ui";

defineProps<{
  filteredManufactureItems: ItemInfo[];
  selectedTargets: string[];
}>();

defineEmits<{
  toggleTarget: [name: string];
}>();
</script>

<template>
  <section>
    <div class="chip-list">
      <UiChip
        v-for="item in filteredManufactureItems"
        :key="item.name"
        :selected="selectedTargets.includes(item.name)"
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
