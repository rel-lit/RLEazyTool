import { ref, type Ref } from "vue";
import type { ItemInfo } from "../../api/client";
import {
  flattenSupplyBuckets,
  flattenTargetBuckets,
  sortBucketWithAnalysisParticipation,
} from "./order";
import { createItemListSession, type ItemListSession } from "./session";
import type { ItemListKind, SupplyBuckets, TargetBuckets } from "./types";

export type ItemListTab = "target" | "supply";

/** 双列表编辑会话 + 当前分析集参与名（供排序规则读取） */
export function createItemListBundle() {
  const targetSession = createItemListSession("target");
  const supplySession = createItemListSession("supply");
  const analysisParticipation = ref<ReadonlySet<string>>(new Set());

  function setAnalysisParticipation(items: readonly string[]): void {
    analysisParticipation.value = new Set(items);
  }

  function sortTargetBuckets(b: TargetBuckets): TargetBuckets {
    const p = analysisParticipation.value;
    return {
      selected: sortBucketWithAnalysisParticipation(b.selected, p),
      normal: sortBucketWithAnalysisParticipation(b.normal, p),
    };
  }

  function sortSupplyBuckets(b: SupplyBuckets): SupplyBuckets {
    const p = analysisParticipation.value;
    return {
      supplied: sortBucketWithAnalysisParticipation(b.supplied, p),
      forbidden: sortBucketWithAnalysisParticipation(b.forbidden, p),
      normal: sortBucketWithAnalysisParticipation(b.normal, p),
    };
  }

  function applySortToSession(
    session: ItemListSession,
    kind: ItemListKind,
    force: boolean
  ): void {
    if (kind === "target") {
      if (!force && !session.dirty.value) return;
      const sorted = sortTargetBuckets(session.targetBuckets.value);
      session.targetBuckets.value = sorted;
      session.displayOrder.value = flattenTargetBuckets(sorted.selected, sorted.normal);
      session.dirty.value = false;
      return;
    }
    if (!force && !session.dirty.value) return;
    const sorted = sortSupplyBuckets(session.supplyBuckets.value);
    session.supplyBuckets.value = sorted;
    session.displayOrder.value = flattenSupplyBuckets(
      sorted.supplied,
      sorted.forbidden,
      sorted.normal
    );
    session.dirty.value = false;
  }

  function commitTargetTab(): void {
    applySortToSession(targetSession, "target", false);
  }

  function commitSupplyTab(): void {
    applySortToSession(supplySession, "supply", false);
  }

  function commitTab(tab: ItemListTab): void {
    if (tab === "target") commitTargetTab();
    else commitSupplyTab();
  }

  /** 布局刷新列表：强制按分析集参与规则重排（无视 dirty） */
  function resortTargetTab(): void {
    applySortToSession(targetSession, "target", true);
  }

  function resortSupplyTab(): void {
    applySortToSession(supplySession, "supply", true);
  }

  function resortAllTabs(): void {
    resortTargetTab();
    resortSupplyTab();
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
    analysisParticipation,
    setAnalysisParticipation,
    commitTargetTab,
    commitSupplyTab,
    commitTab,
    resortTargetTab,
    resortSupplyTab,
    resortAllTabs,
    syncTargetFromCatalog,
    syncSupplyFromCatalog,
    syncAllFromCatalog,
  };
}

export type ItemListBundle = ReturnType<typeof createItemListBundle>;
