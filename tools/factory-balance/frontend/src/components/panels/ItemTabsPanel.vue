<script setup lang="ts">
import { computed, toRef } from "vue";
import type { ItemInfo } from "../../api/client";
import { useItemListsOrchestrator } from "../../domains/item-list";
import UiScrollRegion from "../../ui/primitives/UiScrollRegion.vue";
import CatalogPanel from "./CatalogPanel.vue";
import SupplyPanel from "./SupplyPanel.vue";
import { UiButton, UiIconButton } from "../../ui";

const props = defineProps<{
  targetSearchQuery: string;
  supplySearchQuery: string;
  manufactureItems: ItemInfo[];
  supplyItems: ItemInfo[];
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

const {
  activeTab,
  targetDisplayOrder,
  supplyDisplayOrder,
  tabBarRef,
  targetViewportRef,
  supplyViewportRef,
  switchTab,
  handleToggleTarget,
  handleToggleSupplied,
  handleToggleForbidden,
  onClearSelection,
  canClearSelection,
} = useItemListsOrchestrator({
  manufactureItems: toRef(props, "manufactureItems"),
  supplyItems: toRef(props, "supplyItems"),
  selectedTargets: toRef(props, "selectedTargets"),
  suppliedItems: toRef(props, "suppliedItems"),
  forbiddenItems: toRef(props, "forbiddenItems"),
  onToggleTarget: (name) => emit("toggleTarget", name),
  onToggleSupplied: (name) => emit("toggleSupplied", name),
  onToggleForbidden: (name) => emit("toggleForbidden", name),
  onClearTargets: () => emit("clearTargets"),
  onClearSupplySelections: () => emit("clearSupplySelections"),
});

const activeSearchQuery = computed(() =>
  activeTab.value === "target" ? props.targetSearchQuery : props.supplySearchQuery
);

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
</script>

<template>
  <div class="item-tabs">
    <div ref="tabBarRef" class="ui-tab-bar" role="tablist">
      <UiButton
        variant="tab"
        role="tab"
        :pressed="activeTab === 'target'"
        :aria-selected="activeTab === 'target'"
        @primary="switchTab('target')"
      >
        产出目标
      </UiButton>
      <UiButton
        variant="tab"
        role="tab"
        :pressed="activeTab === 'supply'"
        :aria-selected="activeTab === 'supply'"
        @primary="switchTab('supply')"
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
          @primary="onClearSearch"
        >
          ×
        </UiIconButton>
      </div>
      <UiButton
        variant="danger-soft"
        size="sm"
        :disabled="!canClearSelection"
        @primary="onClearSelection()"
      >
        清空当前选择
      </UiButton>
    </div>

    <UiScrollRegion
      v-show="activeTab === 'target'"
      ref="targetViewportRef"
      class="list-viewport-slot"
    >
      <CatalogPanel
        :display-order="targetDisplayOrder"
        :search-query="targetSearchQuery"
        :selected-targets="selectedTargets"
        @toggle-target="handleToggleTarget"
      />
    </UiScrollRegion>

    <UiScrollRegion
      v-show="activeTab === 'supply'"
      ref="supplyViewportRef"
      class="list-viewport-slot"
    >
      <SupplyPanel
        :display-order="supplyDisplayOrder"
        :search-query="supplySearchQuery"
        :supplied-items="suppliedItems"
        :forbidden-items="forbiddenItems"
        @toggle-supplied="handleToggleSupplied"
        @toggle-forbidden="handleToggleForbidden"
      />
    </UiScrollRegion>
  </div>
</template>

<style scoped>
.item-tabs {
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1;
}

.list-viewport-slot {
  display: flex;
  flex-direction: column;
}
</style>
