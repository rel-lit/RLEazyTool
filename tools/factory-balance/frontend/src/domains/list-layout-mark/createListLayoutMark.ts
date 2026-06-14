import { ref } from "vue";
import type { LayoutRequest, LayoutResponse } from "../../api/client";
import { LIST_LAYOUT_MARK_NONE, type ListLayoutMark, type ItemListSide } from "./types";
import { resolveListLayoutMark } from "./resolveListLayoutMark";

export type { ItemListSide } from "./types";

/**
 * 列表项—布局关联标记：由布局快照推导 chip 右侧透孔圆环及圈内配色。
 * 产出 / 供给各自读取；不写入列表 session 或排序状态。
 */
export function createListLayoutMark() {
  let boundLayout: LayoutResponse | null = null;
  let boundRequest: LayoutRequest | null = null;
  let targetCatalogNames = new Set<string>();
  let supplyCatalogNames = new Set<string>();
  /** 递增以驱动 UI 重绘 */
  const revision = ref(0);

  function bindLayoutSnapshot(
    layout: LayoutResponse,
    request: LayoutRequest,
    manufactureItemNames: ReadonlySet<string>,
    supplyItemNames: ReadonlySet<string>
  ): void {
    boundLayout = layout;
    boundRequest = request;
    targetCatalogNames = new Set(manufactureItemNames);
    supplyCatalogNames = new Set(supplyItemNames);
    revision.value += 1;
  }

  function clearLayoutSnapshot(): void {
    boundLayout = null;
    boundRequest = null;
    targetCatalogNames = new Set();
    supplyCatalogNames = new Set();
    revision.value += 1;
  }

  function analysisItems(): readonly string[] {
    if (!boundLayout || boundLayout.analysis?.impossible) return [];
    return boundLayout.analysis?.analysis_items ?? [];
  }

  /** 产出列表：分析集 ∩ 当前产出 catalog（只读，供排序时传入） */
  function getTargetParticipation(): ReadonlySet<string> {
    const out = new Set<string>();
    for (const name of analysisItems()) {
      if (targetCatalogNames.has(name)) out.add(name);
    }
    return out;
  }

  /** 供给列表：分析集 ∩ 当前供给 catalog（只读，供排序时传入） */
  function getSupplyParticipation(): ReadonlySet<string> {
    const out = new Set<string>();
    for (const name of analysisItems()) {
      if (supplyCatalogNames.has(name)) out.add(name);
    }
    return out;
  }

  function getListLayoutMark(itemName: string, side: ItemListSide): ListLayoutMark {
    const participation =
      side === "target" ? getTargetParticipation() : getSupplyParticipation();
    if (!participation.has(itemName) || !boundLayout || !boundRequest) {
      return LIST_LAYOUT_MARK_NONE;
    }
    return resolveListLayoutMark(itemName, side, boundLayout, boundRequest);
  }

  return {
    revision,
    bindLayoutSnapshot,
    clearLayoutSnapshot,
    getTargetParticipation,
    getSupplyParticipation,
    getListLayoutMark,
  };
}

export type ListLayoutMarkModule = ReturnType<typeof createListLayoutMark>;
