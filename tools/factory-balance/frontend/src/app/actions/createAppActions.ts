import type { LayoutRequest, LayoutResponse } from "../../api/client";
import type { AppContext } from "../context";
import type { ItemListTab } from "../../domains/item-list/itemListBundle";
import {
  createSupplySortKeyResolver,
  createTargetSortKeyResolver,
} from "../../domains/layout-analysis";
import type { ItemSortKeyResolver } from "../../domains/item-list/order";

/**
 * 语义动作层：用业务语言描述「要发生什么」，再调用各业务模块 API。
 * 不含 EventBus 订阅；订阅在 app/wire。
 */
export function createAppActions(ctx: AppContext) {
  /** 布局快照里的 request 与当前勾选/模式对齐，供排序与标记读取 */
  function requestForListContext(base: LayoutRequest): LayoutRequest {
    return {
      ...base,
      supply_mode: ctx.selection.supplyMode.value,
      supplied_items: [...ctx.selection.suppliedItems.value],
      forbidden_items: [...ctx.selection.forbiddenItems.value],
    };
  }

  function sortKeyResolverForTab(
    tab: ItemListTab,
    layout: LayoutResponse,
    request: LayoutRequest
  ): ItemSortKeyResolver {
    const snapshot = { layout, request: requestForListContext(request) };
    return tab === "target"
      ? createTargetSortKeyResolver(snapshot)
      : createSupplySortKeyResolver(snapshot);
  }

  function sortKeyResolverFromMark(tab: ItemListTab): ItemSortKeyResolver | undefined {
    const snap = ctx.listLayoutMark.getLayoutSnapshot();
    if (!snap) return undefined;
    return sortKeyResolverForTab(tab, snap.layout, snap.request);
  }

  /** 无布局：字典序；有布局：参与集 tier/layer/rank */
  function resortItemListsDefault(): void {
    ctx.itemList.resortTargetTab(new Set(), undefined);
    ctx.itemList.resortSupplyTab(new Set(), undefined);
  }

  /** 若已有布局快照，对两侧列表按参与集 + tier/layer/rank 整体重排 */
  function resortItemListsFromSnapshot(): void {
    const snap = ctx.listLayoutMark.getLayoutSnapshot();
    if (!snap) return;
    ctx.itemList.resortTargetTab(
      ctx.listLayoutMark.getTargetParticipation(),
      sortKeyResolverForTab("target", snap.layout, snap.request)
    );
    ctx.itemList.resortSupplyTab(
      ctx.listLayoutMark.getSupplyParticipation(),
      sortKeyResolverForTab("supply", snap.layout, snap.request)
    );
  }

  /** 刷新列表：绑定布局关联标记 + 按分析集参与重排（计算/载入布局后调用） */
  function refreshItemLists(layout: LayoutResponse, request: LayoutRequest): void {
    if (layout.analysis?.impossible) {
      ctx.listLayoutMark.clearLayoutSnapshot();
      ctx.layoutInspection.clear();
      ctx.layoutInspection.setLayout(null);
      return;
    }
    ctx.layoutInspection.setLayout(layout, request);
    const manufactureNames = new Set(
      ctx.catalog.manufactureItems.value.map((i) => i.name)
    );
    const supplyNames = new Set(ctx.catalog.supplyItems.value.map((i) => i.name));
    ctx.listLayoutMark.bindLayoutSnapshot(layout, request, manufactureNames, supplyNames);
    ctx.itemList.resortTargetTab(
      ctx.listLayoutMark.getTargetParticipation(),
      sortKeyResolverForTab("target", layout, request)
    );
    ctx.itemList.resortSupplyTab(
      ctx.listLayoutMark.getSupplyParticipation(),
      sortKeyResolverForTab("supply", layout, request)
    );
  }

  /** 提交列表编辑：区外点击 / 切 tab 时，对指定 tab 落盘排序 */
  function commitItemListTab(tab: ItemListTab): void {
    const participation =
      tab === "target"
        ? ctx.listLayoutMark.getTargetParticipation()
        : ctx.listLayoutMark.getSupplyParticipation();
    ctx.itemList.commitTab(tab, participation, sortKeyResolverFromMark(tab));
  }

  function syncItemListsFromCatalog(): void {
    ctx.itemList.syncAllFromCatalog(
      ctx.catalog.manufactureItems.value,
      ctx.catalog.supplyItems.value,
      ctx.selection.selectedTargets.value,
      ctx.selection.suppliedItems.value,
      ctx.selection.forbiddenItems.value
    );
    if (ctx.listLayoutMark.getLayoutSnapshot()) {
      resortItemListsFromSnapshot();
    } else {
      resortItemListsDefault();
    }
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

  /** 清空产出选择后刷新列表顺序（沿用当前布局参与集） */
  function clearTargetListSelection(): void {
    ctx.selection.clearTargets();
    ctx.itemList.syncTargetFromCatalog(
      ctx.catalog.manufactureItems.value,
      ctx.selection.selectedTargets.value
    );
    ctx.itemList.resortTargetTab(
      ctx.listLayoutMark.getTargetParticipation(),
      sortKeyResolverFromMark("target")
    );
  }

  /** 清空供给选择后刷新列表顺序（沿用当前布局参与集） */
  function clearSupplyListSelection(): void {
    ctx.selection.clearSupplySelections();
    ctx.itemList.syncSupplyFromCatalog(
      ctx.catalog.supplyItems.value,
      ctx.selection.suppliedItems.value,
      ctx.selection.forbiddenItems.value
    );
    ctx.itemList.resortSupplyTab(
      ctx.listLayoutMark.getSupplyParticipation(),
      sortKeyResolverFromMark("supply")
    );
  }

  function setSupplyMode(mode: "raw" | "direct"): void {
    ctx.selection.supplyMode.value = mode;
    ctx.bus.emit({ type: "SelectionChanged", reason: "user-toggle" });
    ctx.itemList.resortSupplyTab(
      ctx.listLayoutMark.getSupplyParticipation(),
      sortKeyResolverFromMark("supply")
    );
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
