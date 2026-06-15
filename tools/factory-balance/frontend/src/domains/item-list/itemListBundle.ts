import type { ItemInfo } from "../../api/client";
import type { ItemSortKeyResolver } from "./order";
import {
  sortSupplyDisplayOrder,
  sortTargetDisplayOrder,
} from "./order";
import { createItemListSession, type ItemListSession } from "./session";
import type { ItemListKind } from "./types";

export type ItemListTab = "target" | "supply";

/** 双列表编辑会话；排序规则在 commit/resort 时由调用方传入参与集（只读） */
export function createItemListBundle() {
  const targetSession = createItemListSession("target");
  const supplySession = createItemListSession("supply");

  function applySortToSession(
    session: ItemListSession,
    kind: ItemListKind,
    force: boolean,
    participation: ReadonlySet<string>,
    sortKeyResolver?: ItemSortKeyResolver
  ): void {
    if (!force && !session.dirty.value) return;

    if (kind === "target") {
      const sorted = sortTargetDisplayOrder(
        session.targetBuckets.value,
        participation,
        sortKeyResolver
      );
      session.targetBuckets.value = sorted.buckets;
      session.displayOrder.value = sorted.displayOrder;
      session.dirty.value = false;
      return;
    }

    const sorted = sortSupplyDisplayOrder(
      session.supplyBuckets.value,
      participation,
      sortKeyResolver
    );
    session.supplyBuckets.value = sorted.buckets;
    session.displayOrder.value = sorted.displayOrder;
    session.dirty.value = false;
  }

  function commitTargetTab(
    participation: ReadonlySet<string>,
    sortKeyResolver?: ItemSortKeyResolver
  ): void {
    applySortToSession(targetSession, "target", false, participation, sortKeyResolver);
  }

  function commitSupplyTab(
    participation: ReadonlySet<string>,
    sortKeyResolver?: ItemSortKeyResolver
  ): void {
    applySortToSession(supplySession, "supply", false, participation, sortKeyResolver);
  }

  function commitTab(
    tab: ItemListTab,
    participation: ReadonlySet<string>,
    sortKeyResolver?: ItemSortKeyResolver
  ): void {
    if (tab === "target") commitTargetTab(participation, sortKeyResolver);
    else commitSupplyTab(participation, sortKeyResolver);
  }

  /** 布局刷新列表：强制按分析集参与规则重排（无视 dirty） */
  function resortTargetTab(
    participation: ReadonlySet<string>,
    sortKeyResolver?: ItemSortKeyResolver
  ): void {
    applySortToSession(targetSession, "target", true, participation, sortKeyResolver);
  }

  function resortSupplyTab(
    participation: ReadonlySet<string>,
    sortKeyResolver?: ItemSortKeyResolver
  ): void {
    applySortToSession(supplySession, "supply", true, participation, sortKeyResolver);
  }

  function syncTargetFromCatalog(
    items: readonly ItemInfo[],
    selectedNames: readonly string[]
  ): void {
    targetSession.initFromCatalog(items, { selectedNames });
  }

  function syncSupplyFromCatalog(
    items: readonly ItemInfo[],
    suppliedNames: readonly string[],
    forbiddenNames: readonly string[]
  ): void {
    supplySession.initFromCatalog(items, {
      suppliedNames,
      forbiddenNames,
    });
  }

  function syncAllFromCatalog(
    manufactureItems: readonly ItemInfo[],
    supplyItems: readonly ItemInfo[],
    selectedNames: readonly string[],
    suppliedNames: readonly string[],
    forbiddenNames: readonly string[]
  ): void {
    syncTargetFromCatalog(manufactureItems, selectedNames);
    syncSupplyFromCatalog(supplyItems, suppliedNames, forbiddenNames);
  }

  return {
    targetDisplayOrder: targetSession.displayOrder,
    supplyDisplayOrder: supplySession.displayOrder,
    targetSession,
    supplySession,
    commitTargetTab,
    commitSupplyTab,
    commitTab,
    resortTargetTab,
    resortSupplyTab,
    syncTargetFromCatalog,
    syncSupplyFromCatalog,
    syncAllFromCatalog,
  };
}

export type ItemListBundle = ReturnType<typeof createItemListBundle>;
