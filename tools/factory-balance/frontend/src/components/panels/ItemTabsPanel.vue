<script setup lang="ts">
import { computed, ref } from "vue";
import type { ItemInfo } from "../../api/client";
import CatalogPanel from "./CatalogPanel.vue";
import SupplyPanel from "./SupplyPanel.vue";

const props = defineProps<{
  targetSearchQuery: string;
  supplySearchQuery: string;
  filteredManufactureItems: ItemInfo[];
  filteredSupplyItems: ItemInfo[];
  selectedTargets: string[];
  suppliedItems: string[];
  forbiddenItems: string[];
}>();

const emit = defineEmits<{
  "update:targetSearchQuery": [value: string];
  "update:supplySearchQuery": [value: string];
  toggleTarget: [name: string];
  toggleSupplied: [name: string];
  toggleForbidden: [name: string];
  clearTargets: [];
  clearSupplySelections: [];
}>();

type ItemTab = "target" | "supply";

const activeTab = ref<ItemTab>("target");

const activeSearchQuery = computed(() =>
  activeTab.value === "target" ? props.targetSearchQuery : props.supplySearchQuery
);

const canClearSelection = computed(() => {
  if (activeTab.value === "target") {
    return props.selectedTargets.length > 0;
  }
  return props.suppliedItems.length > 0 || props.forbiddenItems.length > 0;
});

function onSearchInput(event: Event): void {
  const value = (event.target as HTMLInputElement).value;
  if (activeTab.value === "target") {
    emit("update:targetSearchQuery", value);
  } else {
    emit("update:supplySearchQuery", value);
  }
}

function onClearSearch(): void {
  if (activeTab.value === "target") {
    emit("update:targetSearchQuery", "");
  } else {
    emit("update:supplySearchQuery", "");
  }
}

function onClearSelection(): void {
  if (!canClearSelection.value) return;
  if (activeTab.value === "target") {
    emit("clearTargets");
  } else {
    emit("clearSupplySelections");
  }
}
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

    <div class="tab-toolbar">
      <div class="search-wrap">
        <input
          class="search-input"
          :class="{ 'has-clear': activeSearchQuery.length > 0 }"
          :value="activeSearchQuery"
          placeholder="搜索物品…"
          @input="onSearchInput"
        />
        <button
          v-if="activeSearchQuery.length > 0"
          type="button"
          class="search-clear"
          aria-label="清空搜索"
          @click="onClearSearch"
        >
          ×
        </button>
      </div>
      <button
        type="button"
        class="clear-btn"
        :disabled="!canClearSelection"
        @click="onClearSelection"
      >
        清空当前选择
      </button>
    </div>

    <div class="tab-scroll">
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

.tab-toolbar {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  margin-bottom: 10px;
}

.search-wrap {
  flex: 1;
  min-width: 0;
  position: relative;
}

.search-input {
  width: 100%;
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid #30363d;
  background: #0d1117;
  color: inherit;
}

.search-input.has-clear {
  padding-right: 28px;
}

.search-clear {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: #30363d;
  color: #8b949e;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.search-clear:hover {
  background: #484f58;
  color: #c9d1d9;
}

.clear-btn {
  flex: 1;
  min-width: 0;
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid #30363d;
  background: #21262d;
  color: #c9d1d9;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.clear-btn:not(:disabled) {
  border-color: #6b4548;
  background: #3a2829;
  color: #ddb8b8;
}

.clear-btn:hover:not(:disabled) {
  border-color: #805055;
  background: #452f31;
  color: #eccaca;
}

.clear-btn:disabled {
  border-color: #30363d;
  background: #21262d;
  color: #8b949e;
  opacity: 0.55;
  cursor: not-allowed;
}

.tab-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 2px;
}

.tab-pane {
  min-height: 0;
}
</style>
