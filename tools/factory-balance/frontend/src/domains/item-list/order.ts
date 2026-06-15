import type { ItemInfo } from "../../api/client";
import type { ItemListSortKey } from "../layout-analysis";
import {
  compareSupplyListSortKeys,
  compareTargetListSortKeys,
} from "../layout-analysis";
import type { SupplyBuckets, TargetBuckets } from "./types";

export function compareItemsByLabel(a: ItemInfo, b: ItemInfo): number {
  const byLabel = a.label.localeCompare(b.label, "zh-CN");
  if (byLabel !== 0) return byLabel;
  return a.name.localeCompare(b.name);
}

export function sortBucket(items: readonly ItemInfo[]): ItemInfo[] {
  return [...items].sort(compareItemsByLabel);
}

export type ItemSortKeyResolver = (item: ItemInfo) => ItemListSortKey;

export type BucketPriorityFn = (item: ItemInfo) => number;

/**
 * 对整份展示列排序：先选桶优先级，再参与集前置，参与集内按布局 tier/layer/rank。
 * 其余段（含无布局时整表）：统一 label → name 字典序。
 */
export function sortFlatDisplayOrder(
  items: readonly ItemInfo[],
  bucketPriority: BucketPriorityFn,
  participation: ReadonlySet<string>,
  compareKeys: (a: ItemListSortKey, b: ItemListSortKey) => number,
  sortKeyResolver?: ItemSortKeyResolver
): ItemInfo[] {
  return [...items].sort((a, b) => {
    const byBucket = bucketPriority(a) - bucketPriority(b);
    if (byBucket !== 0) return byBucket;

    const aIn = participation.has(a.name);
    const bIn = participation.has(b.name);
    if (aIn !== bIn) return aIn ? -1 : 1;

    if (aIn && bIn && sortKeyResolver) {
      return compareKeys(sortKeyResolver(a), sortKeyResolver(b));
    }
    return compareItemsByLabel(a, b);
  });
}

function targetBucketPriority(
  buckets: TargetBuckets
): BucketPriorityFn {
  const selected = new Set(buckets.selected.map((i) => i.name));
  return (item) => (selected.has(item.name) ? 0 : 1);
}

function supplyBucketPriority(
  buckets: SupplyBuckets
): BucketPriorityFn {
  const supplied = new Set(buckets.supplied.map((i) => i.name));
  const forbidden = new Set(buckets.forbidden.map((i) => i.name));
  return (item) => {
    if (supplied.has(item.name)) return 0;
    if (forbidden.has(item.name)) return 1;
    return 2;
  };
}

export function sortTargetDisplayOrder(
  buckets: TargetBuckets,
  participation: ReadonlySet<string>,
  sortKeyResolver?: ItemSortKeyResolver
): { buckets: TargetBuckets; displayOrder: ItemInfo[] } {
  const flat = flattenTargetBuckets(buckets.selected, buckets.normal);
  const priority = targetBucketPriority(buckets);
  const displayOrder = sortFlatDisplayOrder(
    flat,
    priority,
    participation,
    compareTargetListSortKeys,
    sortKeyResolver
  );
  const selectedNames = new Set(buckets.selected.map((i) => i.name));
  const selected: ItemInfo[] = [];
  const normal: ItemInfo[] = [];
  for (const item of displayOrder) {
    if (selectedNames.has(item.name)) selected.push(item);
    else normal.push(item);
  }
  return { buckets: { selected, normal }, displayOrder };
}

export function sortSupplyDisplayOrder(
  buckets: SupplyBuckets,
  participation: ReadonlySet<string>,
  sortKeyResolver?: ItemSortKeyResolver
): { buckets: SupplyBuckets; displayOrder: ItemInfo[] } {
  const flat = flattenSupplyBuckets(
    buckets.supplied,
    buckets.forbidden,
    buckets.normal
  );
  const priority = supplyBucketPriority(buckets);
  const displayOrder = sortFlatDisplayOrder(
    flat,
    priority,
    participation,
    compareSupplyListSortKeys,
    sortKeyResolver
  );
  const suppliedNames = new Set(buckets.supplied.map((i) => i.name));
  const forbiddenNames = new Set(buckets.forbidden.map((i) => i.name));
  const supplied: ItemInfo[] = [];
  const forbidden: ItemInfo[] = [];
  const normal: ItemInfo[] = [];
  for (const item of displayOrder) {
    if (suppliedNames.has(item.name)) supplied.push(item);
    else if (forbiddenNames.has(item.name)) forbidden.push(item);
    else normal.push(item);
  }
  return { buckets: { supplied, forbidden, normal }, displayOrder };
}

/** @deprecated 桶内分段排序；请用 sortTargetDisplayOrder */
export function sortBucketWithAnalysisParticipation(
  items: readonly ItemInfo[],
  analysisParticipation: ReadonlySet<string>,
  sortKeyResolver?: ItemSortKeyResolver,
  compareKeys = compareTargetListSortKeys
): ItemInfo[] {
  const priority = () => 0;
  return sortFlatDisplayOrder(
    items,
    priority,
    analysisParticipation,
    compareKeys,
    sortKeyResolver
  );
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
