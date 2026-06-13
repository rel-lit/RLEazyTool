import type { ItemInfo } from "../../api/client";

export type ItemListKind = "target" | "supply";

export type TargetBuckets = {
  selected: ItemInfo[];
  normal: ItemInfo[];
};

export type SupplyBuckets = {
  supplied: ItemInfo[];
  forbidden: ItemInfo[];
  normal: ItemInfo[];
};
