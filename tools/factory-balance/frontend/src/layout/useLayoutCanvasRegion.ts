import { computed, type Ref } from "vue";
import type { LayoutEdge, LayoutNode } from "../../api/client";
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
  onPrimary?: (target: CanvasRegionTarget) => void;
}

/**
 * 布局画布：将 layout 领域 highlight 解析接入统一 canvas region。
 * UI 状态（hover/pin）在此；SBTO 边详情等业务由 LayoutWorkspace 订阅 primary 处理。
 */
export function useLayoutCanvasRegion(
  options: UseLayoutCanvasRegionOptions
): CanvasRegionController<FocusHighlight> & {
  phase: Ref<FocusPhase>;
  overlayKey: Ref<string>;
} {
  const { ctx, onPrimary } = options;

  const region = useCanvasRegion<FocusHighlight>({
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
