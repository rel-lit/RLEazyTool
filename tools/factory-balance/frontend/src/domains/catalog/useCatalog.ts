import { computed, ref } from "vue";
import type { ItemInfo } from "../../api/client";
import type { AppEventBus, CatalogPayload } from "../../app/events";

export function useCatalog(bus: AppEventBus) {
  const mode = ref<"progress" | "full">("progress");
  const manufactureItems = ref<ItemInfo[]>([]);
  const supplyItems = ref<ItemInfo[]>([]);
  const loading = ref(false);
  const searchQuery = ref("");

  const filteredManufactureItems = computed(() => {
    const q = searchQuery.value.trim().toLowerCase();
    const list = manufactureItems.value;
    if (!q) return list;
    return list.filter(
      (i) => i.label.toLowerCase().includes(q) || i.name.toLowerCase().includes(q)
    );
  });

  const filteredSupplyItems = computed(() => {
    const q = searchQuery.value.trim().toLowerCase();
    const list = supplyItems.value;
    if (!q) return list;
    return list.filter(
      (i) => i.label.toLowerCase().includes(q) || i.name.toLowerCase().includes(q)
    );
  });

  function applyPayload(catalog: CatalogPayload): void {
    manufactureItems.value = catalog.manufacture_items;
    supplyItems.value = catalog.supply_items;
  }

  function setMode(next: "progress" | "full"): void {
    mode.value = next;
  }

  function clearSearch(): void {
    searchQuery.value = "";
  }

  bus.on("ProgressChanged", (e) => {
    setMode("progress");
    applyPayload(e.catalog);
    clearSearch();
  });

  bus.on("ProgressCleared", () => {
    manufactureItems.value = [];
    supplyItems.value = [];
  });

  return {
    mode,
    manufactureItems,
    supplyItems,
    loading,
    searchQuery,
    filteredManufactureItems,
    filteredSupplyItems,
    applyPayload,
    setMode,
    clearSearch,
  };
}

export type CatalogModule = ReturnType<typeof useCatalog>;
