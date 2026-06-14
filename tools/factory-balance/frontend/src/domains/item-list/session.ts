import { ref } from "vue";
import type { ItemInfo } from "../../api/client";
import {
  flattenSupplyBuckets,
  flattenTargetBuckets,
} from "./order";
import type { ItemListKind, SupplyBuckets, TargetBuckets } from "./types";

export interface TargetCatalogSelection {
  selectedNames: readonly string[];
}

export interface SupplyCatalogSelection {
  suppliedNames: readonly string[];
  forbiddenNames: readonly string[];
}

export type CatalogSelection = TargetCatalogSelection | SupplyCatalogSelection;

function itemMap(items: readonly ItemInfo[]): Map<string, ItemInfo> {
  return new Map(items.map((i) => [i.name, i]));
}

function removeByName(list: ItemInfo[], name: string): ItemInfo | null {
  const idx = list.findIndex((i) => i.name === name);
  if (idx < 0) return null;
  return list.splice(idx, 1)[0] ?? null;
}

function takeFromTargetBuckets(buckets: TargetBuckets, name: string): ItemInfo | null {
  return removeByName(buckets.selected, name) ?? removeByName(buckets.normal, name);
}

function takeFromSupplyBuckets(buckets: SupplyBuckets, name: string): ItemInfo | null {
  return (
    removeByName(buckets.supplied, name) ??
    removeByName(buckets.forbidden, name) ??
    removeByName(buckets.normal, name)
  );
}

/**
 * 物品列表「编辑会话」：桶状态 + 冻结的 displayOrder。
 */
export function createItemListSession(kind: ItemListKind) {
  const catalogIndex = ref<ItemInfo[]>([]);
  const displayOrder = ref<ItemInfo[]>([]);
  const dirty = ref(false);

  const targetBuckets = ref<TargetBuckets>({ selected: [], normal: [] });
  const supplyBuckets = ref<SupplyBuckets>({ supplied: [], forbidden: [], normal: [] });

  function initFromCatalog(
    items: readonly ItemInfo[],
    selection?: CatalogSelection
  ): void {
    catalogIndex.value = [...items];
    dirty.value = false;

    if (kind === "target") {
      const sel = selection as TargetCatalogSelection | undefined;
      const selectedSet = new Set(sel?.selectedNames ?? []);
      const selected: ItemInfo[] = [];
      const normal: ItemInfo[] = [];
      for (const item of items) {
        if (selectedSet.has(item.name)) selected.push(item);
        else normal.push(item);
      }
      targetBuckets.value = { selected, normal };
      displayOrder.value = flattenTargetBuckets(selected, normal);
      return;
    }

    const sel = selection as SupplyCatalogSelection | undefined;
    const suppliedSet = new Set(sel?.suppliedNames ?? []);
    const forbiddenSet = new Set(sel?.forbiddenNames ?? []);
    const supplied: ItemInfo[] = [];
    const forbidden: ItemInfo[] = [];
    const normal: ItemInfo[] = [];
    for (const item of items) {
      if (suppliedSet.has(item.name)) supplied.push(item);
      else if (forbiddenSet.has(item.name)) forbidden.push(item);
      else normal.push(item);
    }
    supplyBuckets.value = { supplied, forbidden, normal };
    displayOrder.value = flattenSupplyBuckets(supplied, forbidden, normal);
  }

  function applyTargetToggle(name: string, isSelected: boolean): void {
    const b = targetBuckets.value;
    const fromCatalog = itemMap(catalogIndex.value).get(name);
    const item = takeFromTargetBuckets(b, name) ?? fromCatalog;
    if (!item) return;
    if (isSelected) b.selected.push(item);
    else b.normal.push(item);
    dirty.value = true;
  }

  function applySupplyToggle(
    name: string,
    state: "supplied" | "forbidden" | "normal"
  ): void {
    const b = supplyBuckets.value;
    const fromCatalog = itemMap(catalogIndex.value).get(name);
    const item = takeFromSupplyBuckets(b, name) ?? fromCatalog;
    if (!item) return;
    if (state === "supplied") b.supplied.push(item);
    else if (state === "forbidden") b.forbidden.push(item);
    else b.normal.push(item);
    dirty.value = true;
  }

  return {
    kind,
    displayOrder,
    dirty,
    targetBuckets,
    supplyBuckets,
    initFromCatalog,
    applyTargetToggle,
    applySupplyToggle,
  };
}

export type ItemListSession = ReturnType<typeof createItemListSession>;
