import {
  computed,
  inject,
  nextTick,
  onMounted,
  onUnmounted,
  ref,
  watch,
  type Ref,
} from "vue";
import type { ItemInfo } from "../../api/client";
import type { AppEventBus } from "../../app/events";
import { useRegionOutside } from "../../ui";
import { createItemListSession } from "./session";

export type ItemListTab = "target" | "supply";

export interface ItemListsOrchestratorDeps {
  manufactureItems: Ref<ItemInfo[]>;
  supplyItems: Ref<ItemInfo[]>;
  selectedTargets: Ref<string[]>;
  suppliedItems: Ref<string[]>;
  forbiddenItems: Ref<string[]>;
  onToggleTarget: (name: string) => void;
  onToggleSupplied: (name: string) => void;
  onToggleForbidden: (name: string) => void;
  onClearTargets: () => void;
  onClearSupplySelections: () => void;
}

/**
 * 双 tab 物品列表编排：session（全量 catalog）+ 区外 commit + tab 切换。
 * 搜索遮罩在 dumb panel 层处理，不触发 session 重建。
 */
export function useItemListsOrchestrator(deps: ItemListsOrchestratorDeps) {
  const appBus = inject<AppEventBus | null>("appBus", null);

  const activeTab = ref<ItemListTab>("target");
  const targetSession = createItemListSession("target");
  const supplySession = createItemListSession("supply");

  const targetDisplayOrder = targetSession.displayOrder;
  const supplyDisplayOrder = supplySession.displayOrder;

  const tabBarRef = ref<HTMLElement | null>(null);
  const targetViewportRef = ref<{ rootEl: HTMLElement | null; resetScroll: () => void } | null>(
    null
  );
  const supplyViewportRef = ref<{ rootEl: HTMLElement | null; resetScroll: () => void } | null>(
    null
  );

  function syncTargetSession(): void {
    targetSession.initFromCatalog(deps.manufactureItems.value, {
      selectedNames: deps.selectedTargets.value,
    });
  }

  function syncSupplySession(): void {
    supplySession.initFromCatalog(deps.supplyItems.value, {
      suppliedNames: deps.suppliedItems.value,
      forbiddenNames: deps.forbiddenItems.value,
    });
  }

  function syncAllSessions(): void {
    syncTargetSession();
    syncSupplySession();
  }

  watch(() => deps.manufactureItems.value, syncTargetSession);
  watch(() => deps.supplyItems.value, syncSupplySession);

  watch(
    () => deps.selectedTargets.value,
    () => {
      if (!targetSession.dirty.value) syncTargetSession();
    }
  );

  watch(
    () => [deps.suppliedItems.value, deps.forbiddenItems.value] as const,
    () => {
      if (!supplySession.dirty.value) syncSupplySession();
    }
  );

  function activeRegionRoot(): HTMLElement | null {
    const viewport =
      activeTab.value === "target" ? targetViewportRef.value : supplyViewportRef.value;
    return viewport?.rootEl ?? null;
  }

  function commitSession(tab: ItemListTab): void {
    if (tab === "target") targetSession.commit();
    else supplySession.commit();
  }

  function resetViewportScroll(tab: ItemListTab): void {
    const viewport =
      tab === "target" ? targetViewportRef.value : supplyViewportRef.value;
    viewport?.resetScroll();
  }

  function commitActiveSession(): void {
    commitSession(activeTab.value);
    resetViewportScroll(activeTab.value);
  }

  function switchTab(next: ItemListTab): void {
    if (next === activeTab.value) return;
    const prev = activeTab.value;
    activeTab.value = next;
    resetViewportScroll(prev);
    commitSession(prev);
  }

  useRegionOutside(activeRegionRoot, commitActiveSession, {
    ignore: (target) => {
      const bar = tabBarRef.value;
      return bar != null && target instanceof Node && bar.contains(target);
    },
  });

  const canClearSelection = computed(() => {
    if (activeTab.value === "target") {
      return deps.selectedTargets.value.length > 0;
    }
    return (
      deps.suppliedItems.value.length > 0 || deps.forbiddenItems.value.length > 0
    );
  });

  function handleToggleTarget(name: string): void {
    const willSelect = !deps.selectedTargets.value.includes(name);
    deps.onToggleTarget(name);
    targetSession.applyTargetToggle(name, willSelect);
  }

  function handleToggleSupplied(name: string): void {
    const wasSupplied = deps.suppliedItems.value.includes(name);
    deps.onToggleSupplied(name);
    supplySession.applySupplyToggle(name, wasSupplied ? "normal" : "supplied");
  }

  function handleToggleForbidden(name: string): void {
    const wasForbidden = deps.forbiddenItems.value.includes(name);
    deps.onToggleForbidden(name);
    supplySession.applySupplyToggle(name, wasForbidden ? "normal" : "forbidden");
  }

  async function onClearSelection(): Promise<void> {
    if (!canClearSelection.value) return;
    if (activeTab.value === "target") {
      deps.onClearTargets();
      await nextTick();
      syncTargetSession();
    } else {
      deps.onClearSupplySelections();
      await nextTick();
      syncSupplySession();
    }
  }

  const busCleanups: (() => void)[] = [];

  onMounted(() => {
    syncAllSessions();
    if (!appBus) return;
    busCleanups.push(appBus.on("ProgressChanged", syncAllSessions));
    busCleanups.push(appBus.on("CatalogModeChanged", syncAllSessions));
  });

  onUnmounted(() => {
    for (const off of busCleanups) off();
  });

  return {
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
  };
}
