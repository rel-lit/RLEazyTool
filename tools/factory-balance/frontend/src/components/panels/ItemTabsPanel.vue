<script setup lang="ts">
import { computed, inject, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import type { ItemInfo } from "../../api/client";
import type { AppEventBus } from "../../app/events";
import {
  createItemListSession,
} from "../../domains/item-list";
import ItemListViewport from "../item-list/ItemListViewport.vue";
import CatalogPanel from "./CatalogPanel.vue";
import SupplyPanel from "./SupplyPanel.vue";
import { UiButton, UiIconButton, useRegionOutside } from "../../ui";

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

const appBus = inject<AppEventBus | null>("appBus", null);
const activeTab = ref<ItemTab>("target");

const targetSession = createItemListSession("target");
const supplySession = createItemListSession("supply");

/** 须顶层引用，模板才能自动解包 ref */
const targetDisplayOrder = targetSession.displayOrder;
const supplyDisplayOrder = supplySession.displayOrder;

const tabBarRef = ref<HTMLElement | null>(null);
const targetViewportRef = ref<InstanceType<typeof ItemListViewport> | null>(null);
const supplyViewportRef = ref<InstanceType<typeof ItemListViewport> | null>(null);

function activeRegionRoot(): HTMLElement | null {
  const viewport =
    activeTab.value === "target" ? targetViewportRef.value : supplyViewportRef.value;
  return viewport?.rootEl ?? null;
}

function commitSession(tab: ItemTab): void {
  if (tab === "target") targetSession.commit();
  else supplySession.commit();
}

function resetViewportScroll(tab: ItemTab): void {
  const viewport =
    tab === "target" ? targetViewportRef.value : supplyViewportRef.value;
  viewport?.resetScroll();
}

function commitActiveSession(): void {
  commitSession(activeTab.value);
  resetViewportScroll(activeTab.value);
}

function switchTab(next: ItemTab): void {
  if (next === activeTab.value) return;
  const prev = activeTab.value;
  activeTab.value = next;
  resetViewportScroll(prev);
  commitSession(prev);
}

useRegionOutside(
  activeRegionRoot,
  commitActiveSession,
  {
    ignore: (target) => {
      const bar = tabBarRef.value;
      return bar != null && target instanceof Node && bar.contains(target);
    },
  }
);

const activeSearchQuery = computed(() =>
  activeTab.value === "target" ? props.targetSearchQuery : props.supplySearchQuery
);

const canClearSelection = computed(() => {
  if (activeTab.value === "target") {
    return props.selectedTargets.length > 0;
  }
  return props.suppliedItems.length > 0 || props.forbiddenItems.length > 0;
});

function syncTargetSessionFromFilter(): void {
  targetSession.initFromCatalog(props.filteredManufactureItems);
}

function syncSupplySessionFromFilter(): void {
  supplySession.initFromCatalog(props.filteredSupplyItems);
}

function handleToggleTarget(name: string): void {
  const willSelect = !props.selectedTargets.includes(name);
  emit("toggleTarget", name);
  targetSession.applyTargetToggle(name, willSelect);
}

function handleToggleSupplied(name: string): void {
  const wasSupplied = props.suppliedItems.includes(name);
  emit("toggleSupplied", name);
  supplySession.applySupplyToggle(name, wasSupplied ? "normal" : "supplied");
}

function handleToggleForbidden(name: string): void {
  const wasForbidden = props.forbiddenItems.includes(name);
  emit("toggleForbidden", name);
  supplySession.applySupplyToggle(name, wasForbidden ? "normal" : "forbidden");
}

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

async function onClearSelection(): Promise<void> {
  if (!canClearSelection.value) return;
  if (activeTab.value === "target") {
    emit("clearTargets");
    await nextTick();
    syncTargetSessionFromFilter();
  } else {
    emit("clearSupplySelections");
    await nextTick();
    syncSupplySessionFromFilter();
  }
}

watch(
  () => props.filteredManufactureItems,
  () => syncTargetSessionFromFilter(),
  { immediate: true }
);

watch(
  () => props.filteredSupplyItems,
  () => syncSupplySessionFromFilter(),
  { immediate: true }
);

const busCleanups: (() => void)[] = [];

onMounted(() => {
  if (!appBus) return;
  const onCatalogReset = (): void => {
    syncTargetSessionFromFilter();
    syncSupplySessionFromFilter();
  };
  busCleanups.push(appBus.on("ProgressChanged", onCatalogReset));
  busCleanups.push(appBus.on("CatalogModeChanged", onCatalogReset));
});

onUnmounted(() => {
  for (const off of busCleanups) off();
});
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
        @primary="onClearSelection"
      >
        清空当前选择
      </UiButton>
    </div>

    <ItemListViewport
      v-show="activeTab === 'target'"
      ref="targetViewportRef"
      class="list-viewport-slot"
    >
      <CatalogPanel
        :filtered-manufacture-items="targetDisplayOrder"
        :selected-targets="selectedTargets"
        @toggle-target="handleToggleTarget"
      />
    </ItemListViewport>

    <ItemListViewport
      v-show="activeTab === 'supply'"
      ref="supplyViewportRef"
      class="list-viewport-slot"
    >
      <SupplyPanel
        :filtered-supply-items="supplyDisplayOrder"
        :supplied-items="suppliedItems"
        :forbidden-items="forbiddenItems"
        @toggle-supplied="handleToggleSupplied"
        @toggle-forbidden="handleToggleForbidden"
      />
    </ItemListViewport>
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
