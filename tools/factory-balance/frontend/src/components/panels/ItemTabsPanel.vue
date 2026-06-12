<script setup lang="ts">
import { ref } from "vue";
import type { ItemInfo } from "../../api/client";
import CatalogPanel from "./CatalogPanel.vue";
import SupplyPanel from "./SupplyPanel.vue";

defineProps<{
  searchQuery: string;
  filteredManufactureItems: ItemInfo[];
  filteredSupplyItems: ItemInfo[];
  selectedTargets: string[];
  suppliedItems: string[];
  forbiddenItems: string[];
}>();

defineEmits<{
  "update:searchQuery": [value: string];
  toggleTarget: [name: string];
  toggleSupplied: [name: string];
  toggleForbidden: [name: string];
}>();

type ItemTab = "target" | "supply";

const activeTab = ref<ItemTab>("target");
</script>

<template>
  <div class="item-tabs">
    <div class="tab-bar" role="tablist">
      <button
        type="button"
        role="tab"
        class="tab"
        :class="{ active: activeTab === 'target' }"
        :aria-selected="activeTab === 'target'"
        @click="activeTab = 'target'"
      >
        产出目标
      </button>
      <button
        type="button"
        role="tab"
        class="tab"
        :class="{ active: activeTab === 'supply' }"
        :aria-selected="activeTab === 'supply'"
        @click="activeTab = 'supply'"
      >
        已知外部供给
      </button>
    </div>

    <div class="tab-body">
      <input
        :value="searchQuery"
        placeholder="搜索物品…"
        @input="$emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
      />

      <div v-show="activeTab === 'target'" class="tab-pane" role="tabpanel">
        <CatalogPanel
          :filtered-manufacture-items="filteredManufactureItems"
          :selected-targets="selectedTargets"
          @toggle-target="$emit('toggleTarget', $event)"
        />
      </div>

      <div v-show="activeTab === 'supply'" class="tab-pane" role="tabpanel">
        <SupplyPanel
          :filtered-supply-items="filteredSupplyItems"
          :supplied-items="suppliedItems"
          :forbidden-items="forbiddenItems"
          @toggle-supplied="$emit('toggleSupplied', $event)"
          @toggle-forbidden="$emit('toggleForbidden', $event)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.item-tabs {
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1;
}

.tab-bar {
  display: flex;
  gap: 0;
  border-bottom: 1px solid #30363d;
  margin-bottom: 10px;
  flex-shrink: 0;
}

.tab {
  flex: 1;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: #8b949e;
  padding: 8px 6px;
  margin-bottom: -1px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}

.tab:hover {
  color: #c9d1d9;
}

.tab.active {
  color: #58a6ff;
  border-bottom-color: #388bfd;
}

.tab-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 2px;
}

input {
  width: 100%;
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid #30363d;
  background: #0d1117;
  color: inherit;
  margin-bottom: 10px;
}

.tab-pane {
  min-height: 0;
}
</style>
