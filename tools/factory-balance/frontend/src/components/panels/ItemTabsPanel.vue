<script setup lang="ts">
import { computed, inject, ref } from "vue";
import { appActionsKey, itemListKey, listLayoutMarkKey } from "../../app/useApp";
import type { ItemListTab } from "../../domains/item-list/itemListBundle";
import { useRegionOutside } from "../../ui";
import UiScrollRegion from "../../ui/primitives/UiScrollRegion.vue";
import CatalogPanel from "./CatalogPanel.vue";
import SupplyPanel from "./SupplyPanel.vue";
import { UiButton, UiIconButton } from "../../ui";

const props = defineProps<{
  targetSearchQuery: string;
  supplySearchQuery: string;
  selectedTargets: string[];
  suppliedItems: string[];
  forbiddenItems: string[];
}>();

const emit = defineEmits<{
  "update:targetSearchQuery": [value: string];
  "update:supplySearchQuery": [value: string];
}>();

const actions = inject(appActionsKey)!;
const itemList = inject(itemListKey)!;
const listLayoutMark = inject(listLayoutMarkKey)!;

const activeTab = ref<ItemListTab>("target");
const tabBarRef = ref<HTMLElement | null>(null);
const targetViewportRef = ref<{ rootEl: HTMLElement | null; resetScroll: () => void } | null>(null);
const supplyViewportRef = ref<{ rootEl: HTMLElement | null; resetScroll: () => void } | null>(null);

function resolveTargetLayoutMark(name: string) {
  void listLayoutMark.revision.value;
  return listLayoutMark.getListLayoutMark(name, "target");
}

function resolveSupplyLayoutMark(name: string) {
  void listLayoutMark.revision.value;
  return listLayoutMark.getListLayoutMark(name, "supply");
}

function activeRegionRoot(): HTMLElement | null {
  const viewport =
    activeTab.value === "target" ? targetViewportRef.value : supplyViewportRef.value;
  return viewport?.rootEl ?? null;
}

function resetViewportScroll(tab: ItemListTab): void {
  const viewport =
    tab === "target" ? targetViewportRef.value : supplyViewportRef.value;
  viewport?.resetScroll();
}

function commitActiveTab(): void {
  actions.commitItemListTab(activeTab.value);
  resetViewportScroll(activeTab.value);
}

function switchTab(next: ItemListTab): void {
  if (next === activeTab.value) return;
  const prev = activeTab.value;
  activeTab.value = next;
  resetViewportScroll(prev);
  actions.commitItemListTab(prev);
}

useRegionOutside(activeRegionRoot, commitActiveTab, {
  ignore: (target) => {
    const bar = tabBarRef.value;
    return bar != null && target instanceof Node && bar.contains(target);
  },
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

const canClearSelection = computed(() => {
  if (activeTab.value === "target") {
    return props.selectedTargets.length > 0;
  }
  return props.suppliedItems.length > 0 || props.forbiddenItems.length > 0;
});

function onClearSelection(): void {
  if (!canClearSelection.value) return;
  if (activeTab.value === "target") {
    actions.clearTargetListSelection();
  } else {
    actions.clearSupplyListSelection();
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
        :display-order="itemList.targetDisplayOrder"
        :search-query="targetSearchQuery"
        :selected-targets="selectedTargets"
        :resolve-layout-mark="resolveTargetLayoutMark"
        @toggle-target="actions.tapTargetChip($event)"
      />
    </UiScrollRegion>

    <UiScrollRegion
      v-show="activeTab === 'supply'"
      ref="supplyViewportRef"
      class="list-viewport-slot"
    >
      <SupplyPanel
        :display-order="itemList.supplyDisplayOrder"
        :search-query="supplySearchQuery"
        :supplied-items="suppliedItems"
        :forbidden-items="forbiddenItems"
        :resolve-layout-mark="resolveSupplyLayoutMark"
        @toggle-supplied="actions.tapSuppliedChip($event)"
        @toggle-forbidden="actions.tapForbiddenChip($event)"
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
