import { ref } from "vue";
import type { LayoutRequest, LayoutResponse } from "../../api/client";
import { LIST_LAYOUT_MARK_NONE, type ListLayoutMark } from "./types";

/**
 * 列表项—布局关联标记：由布局快照推导 chip 右侧是否显示镂空球等样式。
 * 不耦合列表排序、选中状态或 UI 组件。
 */
export function createListLayoutMark() {
  let boundLayout: LayoutResponse | null = null;
  /** 递增以驱动 UI 重绘 */
  const revision = ref(0);

  function bindLayoutSnapshot(layout: LayoutResponse, _request: LayoutRequest): void {
    boundLayout = layout;
    revision.value += 1;
  }

  function clearLayoutSnapshot(): void {
    boundLayout = null;
    revision.value += 1;
  }

  function getListLayoutMark(itemName: string): ListLayoutMark {
    if (!boundLayout || boundLayout.analysis?.impossible) {
      return LIST_LAYOUT_MARK_NONE;
    }
    const items = boundLayout.analysis?.analysis_items ?? [];
    if (!items.includes(itemName)) {
      return LIST_LAYOUT_MARK_NONE;
    }
    return { kind: "hollow-sphere" };
  }

  return {
    revision,
    bindLayoutSnapshot,
    clearLayoutSnapshot,
    getListLayoutMark,
  };
}

export type ListLayoutMarkModule = ReturnType<typeof createListLayoutMark>;
