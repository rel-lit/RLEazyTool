<script setup lang="ts">
import type { ItemInfo } from "../../api/client";

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
      <button
        v-for="item in filteredManufactureItems"
        :key="item.name"
        class="chip"
        :class="{ on: selectedTargets.includes(item.name) }"
        @click="$emit('toggleTarget', item.name)"
      >
        {{ item.label }}
        <span v-if="item.expansion === 'space-age'" class="tag">SA</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  background: #21262d;
  border: 1px solid #30363d;
  color: inherit;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}

.chip.on {
  background: #1f6feb;
  border-color: #388bfd;
}

.tag {
  margin-left: 4px;
  font-size: 10px;
  opacity: 0.85;
}
</style>
