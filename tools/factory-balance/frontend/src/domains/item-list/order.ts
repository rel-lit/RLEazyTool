import type { ItemInfo } from "../../api/client";

export function compareItemsByLabel(a: ItemInfo, b: ItemInfo): number {
  const byLabel = a.label.localeCompare(b.label, "zh-CN");
  if (byLabel !== 0) return byLabel;
  return a.name.localeCompare(b.name);
}

export function sortBucket(items: readonly ItemInfo[]): ItemInfo[] {
  return [...items].sort(compareItemsByLabel);
}

/** 桶内：分析集参与物品前置，其余后置；两段各自字典序 */
export function sortBucketWithAnalysisParticipation(
  items: readonly ItemInfo[],
  analysisParticipation: ReadonlySet<string>
): ItemInfo[] {
  const inside: ItemInfo[] = [];
  const outside: ItemInfo[] = [];
  for (const item of items) {
    if (analysisParticipation.has(item.name)) inside.push(item);
    else outside.push(item);
  }
  return [...sortBucket(inside), ...sortBucket(outside)];
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
