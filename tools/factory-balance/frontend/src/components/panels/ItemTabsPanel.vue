<script setup lang="ts">
import { computed, ref } from "vue";
import type { ItemInfo } from "../../api/client";
import CatalogPanel from "./CatalogPanel.vue";
import SupplyPanel from "./SupplyPanel.vue";
import { UiButton, UiIconButton } from "../../ui";

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
    <div class="ui-tab-bar" role="tablist">
      <UiButton
        variant="tab"
        role="tab"
        :pressed="activeTab === 'target'"
        :aria-selected="activeTab === 'target'"
        @click="activeTab = 'target'"
      >
        产出目标
      </UiButton>
      <UiButton
        variant="tab"
        role="tab"
        :pressed="activeTab === 'supply'"
        :aria-selected="activeTab === 'supply'"
        @click="activeTab = 'supply'"
      >
        已知外部供给
      </UiButton>
    </div>

    <div class="ui-toolbar-row">
      <div class="ui-search-wrap">
        <input
          class="ui-input"
          :class="{ 'ui-input--with-clear': activeSearchQuery.length > 0 }"
          :value="activeSearchQuery"
          placeholder="搜索物品…"
          @input="onSearchInput"
        />
        <UiIconButton
          v-if="activeSearchQuery.length > 0"
          aria-label="清空搜索"
          @click="onClearSearch"
        >
          ×
        </UiIconButton>
      </div>
      <UiButton
        variant="danger-soft"
        size="sm"
        :disabled="!canClearSelection"
        @click="onClearSelection"
      >
        清空当前选择
      </UiButton>
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
