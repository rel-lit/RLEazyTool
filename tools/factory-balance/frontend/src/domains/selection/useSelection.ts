import { ref } from "vue";
import type { ItemInfo } from "../../api/client";
import type { AppEventBus } from "../../app/events";

export function useSelection(bus: AppEventBus) {
  const selectedTargets = ref<string[]>([]);
  const suppliedItems = ref<string[]>([]);
  const forbiddenItems = ref<string[]>([]);
  const supplyMode = ref<"raw" | "direct">("raw");
  const boundSaveKey = ref<string | null>(null);

  function reset(): void {
    selectedTargets.value = [];
    suppliedItems.value = [];
    forbiddenItems.value = [];
  }

  function pruneGhost(manufacture: ItemInfo[], supply: ItemInfo[]): void {
    const m = new Set(manufacture.map((i) => i.name));
    const s = new Set(supply.map((i) => i.name));
    const prevTargets = selectedTargets.value.length;
    const prevSupplies = suppliedItems.value.length;
    const prevForbidden = forbiddenItems.value.length;
    selectedTargets.value = selectedTargets.value.filter((n) => m.has(n));
    suppliedItems.value = suppliedItems.value.filter((n) => s.has(n));
    forbiddenItems.value = forbiddenItems.value.filter((n) => s.has(n));
    if (
      selectedTargets.value.length !== prevTargets ||
      suppliedItems.value.length !== prevSupplies ||
      forbiddenItems.value.length !== prevForbidden
    ) {
      bus.emit({ type: "SelectionChanged", reason: "pruned" });
    }
  }

  function toggleTarget(name: string): void {
    const idx = selectedTargets.value.indexOf(name);
    if (idx >= 0) selectedTargets.value.splice(idx, 1);
    else selectedTargets.value.push(name);
    bus.emit({ type: "SelectionChanged", reason: "user-toggle" });
  }

  function toggleSupplied(name: string): void {
    const fidx = forbiddenItems.value.indexOf(name);
    if (fidx >= 0) forbiddenItems.value.splice(fidx, 1);
    const idx = suppliedItems.value.indexOf(name);
    if (idx >= 0) suppliedItems.value.splice(idx, 1);
    else suppliedItems.value.push(name);
    bus.emit({ type: "SelectionChanged", reason: "user-toggle" });
  }

  function toggleForbidden(name: string): void {
    const sidx = suppliedItems.value.indexOf(name);
    if (sidx >= 0) suppliedItems.value.splice(sidx, 1);
    const idx = forbiddenItems.value.indexOf(name);
    if (idx >= 0) forbiddenItems.value.splice(idx, 1);
    else forbiddenItems.value.push(name);
    bus.emit({ type: "SelectionChanged", reason: "user-toggle" });
  }

  function clearTargets(): void {
    if (!selectedTargets.value.length) return;
    selectedTargets.value = [];
    bus.emit({ type: "SelectionChanged", reason: "user-clear" });
  }

  function clearSupplySelections(): void {
    if (!suppliedItems.value.length && !forbiddenItems.value.length) return;
    suppliedItems.value = [];
    forbiddenItems.value = [];
    bus.emit({ type: "SelectionChanged", reason: "user-clear" });
  }

  bus.on("ProgressChanged", (e) => {
    boundSaveKey.value = e.saveKey;
    reset();
    bus.emit({ type: "SelectionChanged", reason: "reset" });
  });

  bus.on("ProgressCleared", () => {
    boundSaveKey.value = null;
    reset();
    bus.emit({ type: "SelectionChanged", reason: "reset" });
  });

  return {
    selectedTargets,
    suppliedItems,
    forbiddenItems,
    supplyMode,
    boundSaveKey,
    reset,
    pruneGhost,
    toggleTarget,
    toggleSupplied,
    toggleForbidden,
    clearTargets,
    clearSupplySelections,
  };
}

export type SelectionModule = ReturnType<typeof useSelection>;
