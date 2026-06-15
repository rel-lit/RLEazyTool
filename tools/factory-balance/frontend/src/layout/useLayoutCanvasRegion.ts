import { computed, type Ref } from "vue";
import type { LayoutEdge, LayoutNode } from "../../api/client";
import type { PinHighlightController } from "../ui/interaction/usePinHighlight";
import { useCanvasRegion, type CanvasRegionController } from "../ui/interaction/canvas/useCanvasRegion";
import type { CanvasRegionTarget } from "../ui/interaction/canvas/types";
import {
  focusFromEdge,
  focusFromNode,
  hiddenOverlayKey,
  type FocusHighlight,
} from "./focus/focusModel";
import { phaseForHighlight, type FocusPhase } from "./focus/focusPhase";

export interface LayoutCanvasRegionContext {
  nodes: Ref<LayoutNode[]>;
  edges: Ref<LayoutEdge[]>;
  productEdges: Ref<LayoutEdge[]>;
  hiddenEdges: Ref<LayoutEdge[]>;
}

export interface UseLayoutCanvasRegionOptions {
  ctx: LayoutCanvasRegionContext;
  pin: PinHighlightController<FocusHighlight>;
  onPrimary?: (target: CanvasRegionTarget) => void;
}

/**
 * 布局画布：将 layout 领域 highlight 解析接入统一 canvas region。
 * pin 状态由 layout-inspection 会话持有；本模块只做 resolver 接线。
 */
export function useLayoutCanvasRegion(
  options: UseLayoutCanvasRegionOptions
): CanvasRegionController<FocusHighlight> & {
  phase: Ref<FocusPhase>;
  overlayKey: Ref<string>;
} {
  const { ctx, pin, onPrimary } = options;

  const region = useCanvasRegion<FocusHighlight>({
    pin,
    onPrimary,
    resolver: {
      resolveNode: (nodeId) =>
        focusFromNode(
          nodeId,
          ctx.productEdges.value,
          ctx.hiddenEdges.value,
          ctx.edges.value,
          ctx.nodes.value
        ),
      resolveEdge: (edgeId) => {
        const le = ctx.edges.value.find((e) => e.id === edgeId);
        if (!le) return null;
        return focusFromEdge(le, ctx.edges.value);
      },
    },
  });

  const phase = computed<FocusPhase>(() => {
    if (region.dragging.value) return "dragging";
    return phaseForHighlight(region.highlight.value);
  });

  const overlayKey = computed(() => hiddenOverlayKey(region.highlight.value));

  return {
    ...region,
    phase,
    overlayKey,
  };
}

export type LayoutCanvasRegionController = ReturnType<typeof useLayoutCanvasRegion>;
