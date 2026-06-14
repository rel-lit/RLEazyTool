import type { LayoutRequest, LayoutResponse } from "../api/client";
import type { AppContext } from "./context";
import type { ItemListTab } from "../domains/item-list/itemListBundle";

/**
 * 语义动作层：用业务语言描述「要发生什么」，再调用各业务模块 API。
 * 不含 EventBus 订阅；订阅在 app/wire。
 */
export function createAppActions(ctx: AppContext) {
  /** 刷新列表：绑定布局关联标记 + 按分析集参与重排（计算/载入布局后调用） */
  function refreshItemLists(layout: LayoutResponse, request: LayoutRequest): void {
    if (layout.analysis?.impossible) {
      ctx.listLayoutMark.clearLayoutSnapshot();
      return;
    }
    const participation = layout.analysis?.analysis_items ?? [];
    ctx.listLayoutMark.bindLayoutSnapshot(layout, request);
    ctx.itemList.setAnalysisParticipation(participation);
    ctx.itemList.resortAllTabs();
  }

  /** 提交列表编辑：区外点击 / 切 tab 时，对指定 tab 落盘排序 */
  function commitItemListTab(tab: ItemListTab): void {
    ctx.itemList.commitTab(tab);
  }

  function syncItemListsFromCatalog(): void {
    ctx.itemList.syncAllFromCatalog(
      ctx.catalog.manufactureItems.value,
      ctx.catalog.supplyItems.value,
      ctx.selection.selectedTargets.value,
      ctx.selection.suppliedItems.value,
      ctx.selection.forbiddenItems.value
    );
  }

  function tapTargetChip(name: string): void {
    const willSelect = !ctx.selection.selectedTargets.value.includes(name);
    ctx.selection.toggleTarget(name);
    ctx.itemList.targetSession.applyTargetToggle(name, willSelect);
  }

  function tapSuppliedChip(name: string): void {
    const wasSupplied = ctx.selection.suppliedItems.value.includes(name);
    ctx.selection.toggleSupplied(name);
    ctx.itemList.supplySession.applySupplyToggle(
      name,
      wasSupplied ? "normal" : "supplied"
    );
  }

  function tapForbiddenChip(name: string): void {
    const wasForbidden = ctx.selection.forbiddenItems.value.includes(name);
    ctx.selection.toggleForbidden(name);
    ctx.itemList.supplySession.applySupplyToggle(
      name,
      wasForbidden ? "normal" : "forbidden"
    );
  }

  function clearTargetListSelection(): void {
    ctx.selection.clearTargets();
    ctx.itemList.syncTargetFromCatalog(
      ctx.catalog.manufactureItems.value,
      ctx.selection.selectedTargets.value
    );
  }

  function clearSupplyListSelection(): void {
    ctx.selection.clearSupplySelections();
    ctx.itemList.syncSupplyFromCatalog(
      ctx.catalog.supplyItems.value,
      ctx.selection.suppliedItems.value,
      ctx.selection.forbiddenItems.value
    );
  }

  function setSupplyMode(mode: "raw" | "direct"): void {
    ctx.selection.supplyMode.value = mode;
    ctx.bus.emit({ type: "SelectionChanged", reason: "user-toggle" });
  }

  return {
    refreshItemLists,
    commitItemListTab,
    syncItemListsFromCatalog,
    tapTargetChip,
    tapSuppliedChip,
    tapForbiddenChip,
    clearTargetListSelection,
    clearSupplyListSelection,
    setSupplyMode,
  };
}

export type AppActions = ReturnType<typeof createAppActions>;
