import type { ItemInfo } from "../../api/client";

export function compareItemsByLabel(a: ItemInfo, b: ItemInfo): number {
  const byLabel = a.label.localeCompare(b.label, "zh-CN");
  if (byLabel !== 0) return byLabel;
  return a.name.localeCompare(b.name);
}

export function sortBucket(items: readonly ItemInfo[]): ItemInfo[] {
  return [...items].sort(compareItemsByLabel);
}

export function flattenTargetBuckets(
  selected: readonly ItemInfo[],
  normal: readonly ItemInfo[]
): ItemInfo[] {
  return [...selected, ...normal];
}

export function flattenSupplyBuckets(
  supplied: readonly ItemInfo[],
  forbidden: readonly ItemInfo[],
  normal: readonly ItemInfo[]
): ItemInfo[] {
  return [...supplied, ...forbidden, ...normal];
}
