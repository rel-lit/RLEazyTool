import { computed, ref } from "vue";
import type { ItemInfo } from "../../api/client";
import type { CatalogPayload } from "../../app/events";

function filterItems(list: ItemInfo[], q: string): ItemInfo[] {
  const needle = q.trim().toLowerCase();
  if (!needle) return list;
  return list.filter(
    (i) => i.label.toLowerCase().includes(needle) || i.name.toLowerCase().includes(needle)
  );
}

export function useCatalog() {
  const mode = ref<"progress" | "full">("progress");
  const manufactureItems = ref<ItemInfo[]>([]);
  const supplyItems = ref<ItemInfo[]>([]);
  const loading = ref(false);
  const targetSearchQuery = ref("");
  const supplySearchQuery = ref("");

  const filteredManufactureItems = computed(() =>
    filterItems(manufactureItems.value, targetSearchQuery.value)
  );

  const filteredSupplyItems = computed(() =>
    filterItems(supplyItems.value, supplySearchQuery.value)
  );

  function applyPayload(catalog: CatalogPayload): void {
    manufactureItems.value = catalog.manufacture_items;
    supplyItems.value = catalog.supply_items;
  }

  function applyProgressCatalog(catalog: CatalogPayload): void {
    mode.value = "progress";
    applyPayload(catalog);
    clearSearch();
  }

  function clearCatalog(): void {
    manufactureItems.value = [];
    supplyItems.value = [];
  }

  function setMode(next: "progress" | "full"): void {
    mode.value = next;
  }

  function clearSearch(): void {
    targetSearchQuery.value = "";
    supplySearchQuery.value = "";
  }

  return {
    mode,
    manufactureItems,
    supplyItems,
    loading,
    targetSearchQuery,
    supplySearchQuery,
    filteredManufactureItems,
    filteredSupplyItems,
    applyPayload,
    applyProgressCatalog,
    clearCatalog,
    setMode,
    clearSearch,
  };
}

export type CatalogModule = ReturnType<typeof useCatalog>;
