import { computed, type Ref } from "vue";
import { usePinHighlight } from "../usePinHighlight";
import type { CanvasHighlightResolver, CanvasRegionTarget } from "./types";

export interface UseCanvasRegionOptions<THighlight> {
  resolver: CanvasHighlightResolver<THighlight>;
  /** 区内 primary（click）——仅 UI 语义；业务在编排层订阅 */
  onPrimary?: (target: CanvasRegionTarget) => void;
  leaveDelayMs?: number;
}

/**
 * 画布交互区：Vue Flow 事件 → 统一 hover/pin 状态机 → optional primary 回调。
 * 高亮 payload 由 layout 层 resolver 提供，本模块不含 SBTO/子树等领域逻辑。
 */
export function useCanvasRegion<THighlight>(options: UseCanvasRegionOptions<THighlight>) {
  const pin = usePinHighlight<THighlight>({ leaveDelayMs: options.leaveDelayMs });

  function resolveEdgeHighlight(edgeId: string): THighlight | null {
    return options.resolver.resolveEdge(edgeId);
  }

  function onNodeEnter(nodeId: string): void {
    pin.hover(options.resolver.resolveNode(nodeId));
  }

  function onNodeLeave(): void {
    pin.scheduleLeave();
  }

  function onEdgeEnter(edgeId: string): void {
    const h = resolveEdgeHighlight(edgeId);
    if (h) pin.hover(h);
  }

  function onEdgeLeave(): void {
    pin.scheduleLeave();
  }

  function onNodeClick(nodeId: string): void {
    pin.pin(options.resolver.resolveNode(nodeId));
    options.onPrimary?.({ kind: "node", id: nodeId });
  }

  function onEdgeClick(edgeId: string): void {
    const h = resolveEdgeHighlight(edgeId);
    if (!h) return;
    pin.pin(h);
    options.onPrimary?.({ kind: "edge", id: edgeId });
  }

  function onPaneClick(): void {
    pin.clear();
    options.onPrimary?.({ kind: "pane" });
  }

  function onDragStart(): void {
    pin.dragStart();
  }

  function onDragStop(): void {
    pin.dragEnd();
  }

  return {
    highlight: pin.highlight,
    isPinned: pin.isPinned,
    dragging: pin.dragging,
    clear: pin.clear,
    handlers: {
      onNodeEnter,
      onNodeLeave,
      onEdgeEnter,
      onEdgeLeave,
      onNodeClick,
      onEdgeClick,
      onPaneClick,
      onDragStart,
      onDragStop,
    },
  };
}

export type CanvasRegionController<THighlight> = ReturnType<typeof useCanvasRegion<THighlight>>;

/** 供 layout 层推导 overlayKey 等 derived UI 状态 */
export function useCanvasRegionHighlight<THighlight>(
  highlight: Ref<THighlight | null>
) {
  return computed(() => highlight.value);
}
