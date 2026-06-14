import { ref } from "vue";
import type { LayoutRequest, LayoutResponse } from "../../api/client";
import { normalizeAnalysisSummary } from "../layout-analysis/normalizeAnalysis";
import { LIST_LAYOUT_MARK_NONE, type ListLayoutMark, type ItemListSide } from "./types";
import { resolveListLayoutMark } from "./resolveListLayoutMark";

export type { ItemListSide } from "./types";

export type LayoutSnapshotRef = {
  layout: LayoutResponse;
  request: LayoutRequest;
};

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

  function getLayoutSnapshot(): LayoutSnapshotRef | null {
    if (!boundLayout || !boundRequest) return null;
    return { layout: boundLayout, request: boundRequest };
  }

  function analysisItems(): readonly string[] {
    if (!boundLayout || boundLayout.analysis?.impossible) return [];
    return normalizeAnalysisSummary(boundLayout.analysis)?.analysis_items ?? [];
  }

  /** 产出列表：分析集 ∪ 被降级声明终端（∩ catalog），供排序「段内优先」 */
  function getTargetParticipation(): ReadonlySet<string> {
    const out = new Set<string>();
    for (const name of analysisItems()) {
      if (targetCatalogNames.has(name)) out.add(name);
    }
    const analysis = boundLayout
      ? normalizeAnalysisSummary(boundLayout.analysis)
      : null;
    if (analysis) {
      for (const name of analysis.demoted_outputs) {
        if (targetCatalogNames.has(name)) out.add(name);
      }
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

  function isTargetMarkEligible(itemName: string): boolean {
    if (!targetCatalogNames.has(itemName) || !boundLayout || !boundRequest) {
      return false;
    }
    if (getTargetParticipation().has(itemName)) return true;
    const analysis = normalizeAnalysisSummary(boundLayout.analysis);
    return analysis?.demoted_outputs.includes(itemName) ?? false;
  }

  function isSupplyMarkEligible(itemName: string): boolean {
    if (!supplyCatalogNames.has(itemName) || !boundLayout || !boundRequest) {
      return false;
    }
    return getSupplyParticipation().has(itemName);
  }

  function getListLayoutMark(itemName: string, side: ItemListSide): ListLayoutMark {
    if (!boundLayout || !boundRequest) {
      return LIST_LAYOUT_MARK_NONE;
    }
    const eligible =
      side === "target" ? isTargetMarkEligible(itemName) : isSupplyMarkEligible(itemName);
    if (!eligible) {
      return LIST_LAYOUT_MARK_NONE;
    }
    return resolveListLayoutMark(itemName, side, boundLayout, boundRequest);
  }

  return {
    revision,
    bindLayoutSnapshot,
    clearLayoutSnapshot,
    getLayoutSnapshot,
    getTargetParticipation,
    getSupplyParticipation,
    getListLayoutMark,
  };
}

export type ListLayoutMarkModule = ReturnType<typeof createListLayoutMark>;
