/**
 * 列表整体排序：桶优先级 → 参与集 → tier/layer/rank
 * 运行：npx tsx tests/order-sort.test.ts（需在 frontend 目录）
 */
import assert from "node:assert/strict";
import {
  sortFlatDisplayOrder,
  sortTargetDisplayOrder,
} from "../src/domains/item-list/order";
import {
  compareTargetListSortKeys,
  TARGET_LIST_TIER,
} from "../src/domains/layout-analysis";
import type { ItemInfo } from "../src/api/client";
import type { ItemListSortKey } from "../src/domains/layout-analysis";

function item(name: string, label = name): ItemInfo {
  return { name, label, type: "item" };
}

function key(
  tier: number,
  layer: number,
  rank: number,
  label: string,
  name: string
): ItemListSortKey {
  return { tier, layer, rank, rankFrac: 0, label, name };
}

const participation = new Set(["terminal-a", "mid-b", "mid-c"]);

const resolver = (i: ItemInfo): ItemListSortKey => {
  switch (i.name) {
    case "terminal-a":
      return key(TARGET_LIST_TIER.EFFECTIVE_TERMINAL, 3, 0, i.label, i.name);
    case "mid-b":
      return key(TARGET_LIST_TIER.INTERMEDIATE, 2, 1, i.label, i.name);
    case "mid-c":
      return key(TARGET_LIST_TIER.INTERMEDIATE, 1, 0, i.label, i.name);
    default:
      return key(TARGET_LIST_TIER.OUTSIDE, -1, 0, i.label, i.name);
  }
};

// 参与集内：终端 → 高 layer 中间物 → 低 layer 中间物
const sorted = sortFlatDisplayOrder(
  [
    item("mid-c", "C"),
    item("other-z", "Z"),
    item("terminal-a", "A"),
    item("mid-b", "B"),
  ],
  () => 0,
  participation,
  compareTargetListSortKeys,
  resolver
);
assert.deepEqual(
  sorted.map((i) => i.name),
  ["terminal-a", "mid-b", "mid-c", "other-z"]
);

// 已选桶始终在未选桶之前，桶内仍按布局序
const buckets = sortTargetDisplayOrder(
  {
    selected: [item("mid-c", "C")],
    normal: [item("terminal-a", "A"), item("other-z", "Z"), item("mid-b", "B")],
  },
  participation,
  resolver
);
assert.deepEqual(
  buckets.displayOrder.map((i) => i.name),
  ["mid-c", "terminal-a", "mid-b", "other-z"]
);

// 无布局：统一字典序
const dictSorted = sortFlatDisplayOrder(
  [item("z-last", "Z末"), item("a-first", "A首"), item("m-mid", "M中")],
  () => 0,
  new Set(),
  compareTargetListSortKeys,
  undefined
);
assert.deepEqual(
  dictSorted.map((i) => i.name),
  ["a-first", "m-mid", "z-last"]
);

console.log("order-sort.test.ts OK");
