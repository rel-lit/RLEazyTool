import type { ItemInfo } from "../../api/client";
import type { ItemListSortKey } from "../layout-analysis";
import {
  compareSupplyListSortKeys,
  compareTargetListSortKeys,
} from "../layout-analysis";

export function compareItemsByLabel(a: ItemInfo, b: ItemInfo): number {
  const byLabel = a.label.localeCompare(b.label, "zh-CN");
  if (byLabel !== 0) return byLabel;
  return a.name.localeCompare(b.name);
}

export function sortBucket(items: readonly ItemInfo[]): ItemInfo[] {
  return [...items].sort(compareItemsByLabel);
}

export type ItemSortKeyResolver = (item: ItemInfo) => ItemListSortKey;

function sortInsideBucket(
  items: readonly ItemInfo[],
  compareKeys: (a: ItemListSortKey, b: ItemListSortKey) => number,
  sortKeyResolver?: ItemSortKeyResolver
): ItemInfo[] {
  if (!sortKeyResolver) {
    return sortBucket(items);
  }
  return [...items].sort((a, b) =>
    compareKeys(sortKeyResolver(a), sortKeyResolver(b))
  );
}

/** 桶内：分析集参与物品前置（按布局 tier/layer/rank），其余后置；段内字典序 */
export function sortBucketWithAnalysisParticipation(
  items: readonly ItemInfo[],
  analysisParticipation: ReadonlySet<string>,
  sortKeyResolver?: ItemSortKeyResolver,
  compareKeys = compareTargetListSortKeys
): ItemInfo[] {
  const inside: ItemInfo[] = [];
  const outside: ItemInfo[] = [];
  for (const item of items) {
    if (analysisParticipation.has(item.name)) inside.push(item);
    else outside.push(item);
  }
  return [
    ...sortInsideBucket(inside, compareKeys, sortKeyResolver),
    ...sortBucket(outside),
  ];
}

export function sortTargetBucketWithAnalysisParticipation(
  items: readonly ItemInfo[],
  analysisParticipation: ReadonlySet<string>,
  sortKeyResolver?: ItemSortKeyResolver
): ItemInfo[] {
  return sortBucketWithAnalysisParticipation(
    items,
    analysisParticipation,
    sortKeyResolver,
    compareTargetListSortKeys
  );
}

export function sortSupplyBucketWithAnalysisParticipation(
  items: readonly ItemInfo[],
  analysisParticipation: ReadonlySet<string>,
  sortKeyResolver?: ItemSortKeyResolver
): ItemInfo[] {
  return sortBucketWithAnalysisParticipation(
    items,
    analysisParticipation,
    sortKeyResolver,
    compareSupplyListSortKeys
  );
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
