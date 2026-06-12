<script setup lang="ts">
import type { ItemInfo } from "../../api/client";

defineProps<{
  filteredSupplyItems: ItemInfo[];
  suppliedItems: string[];
  forbiddenItems: string[];
}>();

defineEmits<{
  toggleSupplied: [name: string];
  toggleForbidden: [name: string];
}>();
</script>

<template>
  <section>
    <p class="hint">左键：已知供给 · 右键：禁止供给</p>
    <div class="chip-list">
      <button
        v-for="item in filteredSupplyItems"
        :key="'s-' + item.name"
        class="chip small"
        :class="{
          on: suppliedItems.includes(item.name),
          forbidden: forbiddenItems.includes(item.name),
        }"
        @click="$emit('toggleSupplied', item.name)"
        @contextmenu.prevent="$emit('toggleForbidden', item.name)"
      >
        {{ item.label }}
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

.chip.small {
  font-size: 11px;
  padding: 3px 8px;
}

.chip.on {
  background: #1f6feb;
  border-color: #388bfd;
}

.chip.forbidden {
  background: #3d1214;
  border-color: #f85149;
  color: #ffb4b4;
  text-decoration: line-through;
}

.hint {
  font-size: 12px;
  color: #8b949e;
  margin: 0 0 8px;
}
</style>
