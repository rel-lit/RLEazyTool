import { ref } from "vue";
import type { ItemInfo } from "../../api/client";
import {
  flattenSupplyBuckets,
  flattenTargetBuckets,
  sortBucket,
} from "./order";
import type { ItemListKind, SupplyBuckets, TargetBuckets } from "./types";

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
 * 与 selection 域、DOM 焦点、commit 触发器均无耦合。
 */
export function createItemListSession(kind: ItemListKind) {
  const catalogIndex = ref<ItemInfo[]>([]);
  /** 渲染顺序；会话内点击只改桶与 selection 样式，不改此列，直到 commit */
  const displayOrder = ref<ItemInfo[]>([]);
  const dirty = ref(false);

  const targetBuckets = ref<TargetBuckets>({ selected: [], normal: [] });
  const supplyBuckets = ref<SupplyBuckets>({ supplied: [], forbidden: [], normal: [] });

  function initFromCatalog(items: readonly ItemInfo[]): void {
    catalogIndex.value = [...items];
    displayOrder.value = [...items];
    dirty.value = false;
    if (kind === "target") {
      targetBuckets.value = { selected: [], normal: [...items] };
    } else {
      supplyBuckets.value = { supplied: [], forbidden: [], normal: [...items] };
    }
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

  /** 区外 pointer 提交：桶内字典序 → displayOrder */
  function commit(): void {
    if (!dirty.value) return;

    if (kind === "target") {
      const b = targetBuckets.value;
      const sorted: TargetBuckets = {
        selected: sortBucket(b.selected),
        normal: sortBucket(b.normal),
      };
      targetBuckets.value = sorted;
      displayOrder.value = flattenTargetBuckets(sorted.selected, sorted.normal);
    } else {
      const b = supplyBuckets.value;
      const sorted: SupplyBuckets = {
        supplied: sortBucket(b.supplied),
        forbidden: sortBucket(b.forbidden),
        normal: sortBucket(b.normal),
      };
      supplyBuckets.value = sorted;
      displayOrder.value = flattenSupplyBuckets(
        sorted.supplied,
        sorted.forbidden,
        sorted.normal
      );
    }
    dirty.value = false;
  }

  return {
    displayOrder,
    dirty,
    initFromCatalog,
    applyTargetToggle,
    applySupplyToggle,
    commit,
  };
}

export type ItemListSession = ReturnType<typeof createItemListSession>;
