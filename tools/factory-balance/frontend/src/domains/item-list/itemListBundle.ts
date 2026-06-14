import type { ItemInfo } from "../../api/client";
import {
  flattenSupplyBuckets,
  flattenTargetBuckets,
  sortBucketWithAnalysisParticipation,
} from "./order";
import { createItemListSession, type ItemListSession } from "./session";
import type { ItemListKind, SupplyBuckets, TargetBuckets } from "./types";

export type ItemListTab = "target" | "supply";

/** 双列表编辑会话；排序规则在 commit/resort 时由调用方传入参与集（只读） */
export function createItemListBundle() {
  const targetSession = createItemListSession("target");
  const supplySession = createItemListSession("supply");

  function sortTargetBuckets(
    b: TargetBuckets,
    participation: ReadonlySet<string>
  ): TargetBuckets {
    return {
      selected: sortBucketWithAnalysisParticipation(b.selected, participation),
      normal: sortBucketWithAnalysisParticipation(b.normal, participation),
    };
  }

  function sortSupplyBuckets(
    b: SupplyBuckets,
    participation: ReadonlySet<string>
  ): SupplyBuckets {
    return {
      supplied: sortBucketWithAnalysisParticipation(b.supplied, participation),
      forbidden: sortBucketWithAnalysisParticipation(b.forbidden, participation),
      normal: sortBucketWithAnalysisParticipation(b.normal, participation),
    };
  }

  function applySortToSession(
    session: ItemListSession,
    kind: ItemListKind,
    force: boolean,
    participation: ReadonlySet<string>
  ): void {
    if (kind === "target") {
      if (!force && !session.dirty.value) return;
      const sorted = sortTargetBuckets(session.targetBuckets.value, participation);
      session.targetBuckets.value = sorted;
      session.displayOrder.value = flattenTargetBuckets(sorted.selected, sorted.normal);
      session.dirty.value = false;
      return;
    }
    if (!force && !session.dirty.value) return;
    const sorted = sortSupplyBuckets(session.supplyBuckets.value, participation);
    session.supplyBuckets.value = sorted;
    session.displayOrder.value = flattenSupplyBuckets(
      sorted.supplied,
      sorted.forbidden,
      sorted.normal
    );
    session.dirty.value = false;
  }

  function commitTargetTab(participation: ReadonlySet<string>): void {
    applySortToSession(targetSession, "target", false, participation);
  }

  function commitSupplyTab(participation: ReadonlySet<string>): void {
    applySortToSession(supplySession, "supply", false, participation);
  }

  function commitTab(tab: ItemListTab, participation: ReadonlySet<string>): void {
    if (tab === "target") commitTargetTab(participation);
    else commitSupplyTab(participation);
  }

  /** 布局刷新列表：强制按分析集参与规则重排（无视 dirty） */
  function resortTargetTab(participation: ReadonlySet<string>): void {
    applySortToSession(targetSession, "target", true, participation);
  }

  function resortSupplyTab(participation: ReadonlySet<string>): void {
    applySortToSession(supplySession, "supply", true, participation);
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
