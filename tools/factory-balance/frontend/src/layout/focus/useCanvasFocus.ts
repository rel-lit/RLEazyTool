import { computed, ref, type Ref } from "vue";
import type { LayoutEdge, LayoutNode } from "../../api/client";
import {
  focusDebugLog,
  focusDebugSummary,
} from "../focusDebug";
import {
  focusFromEdge,
  focusFromNode,
  hiddenOverlayKey,
  type FocusHighlight,
} from "./focusModel";
import {
  effectiveHighlight,
  focusReducer,
  initialFocusState,
  phaseForHighlight,
  type FocusMachineState,
  type FocusPhase,
} from "./focusStateMachine";

export interface CanvasFocusContext {
  nodes: Ref<LayoutNode[]>;
  edges: Ref<LayoutEdge[]>;
  productEdges: Ref<LayoutEdge[]>;
  hiddenEdges: Ref<LayoutEdge[]>;
}

const LEAVE_DELAY_MS = 120;

export function useCanvasFocus(ctx: CanvasFocusContext) {
  const machine = ref<FocusMachineState>({ ...initialFocusState });
  let leaveTimer: ReturnType<typeof setTimeout> | null = null;

  const highlight = computed<FocusHighlight | null>(() =>
    effectiveHighlight(machine.value)
  );

  const phase = computed<FocusPhase>(() => {
    if (machine.value.dragging) return "dragging";
    return phaseForHighlight(highlight.value);
  });

  const isPinned = computed(() => machine.value.pinnedHighlight != null);

  const overlayKey = computed(() => hiddenOverlayKey(highlight.value));

  function cancelLeave() {
    if (leaveTimer) {
      clearTimeout(leaveTimer);
      leaveTimer = null;
    }
  }

  function dispatch(action: Parameters<typeof focusReducer>[1], source: string) {
    if (machine.value.dragging && action.type !== "DRAG_END") {
      return;
    }
    machine.value = focusReducer(machine.value, action);
    focusDebugLog({
      kind: "focus",
      focus: highlight.value,
    });
    if (import.meta.env.DEV) {
      void source;
    }
  }

  function hoverNode(nodeId: string, source: string) {
    cancelLeave();
    dispatch(
      {
        type: "HOVER_NODE",
        highlight: focusFromNode(
          nodeId,
          ctx.productEdges.value,
          ctx.hiddenEdges.value,
          ctx.edges.value,
          ctx.nodes.value
        ),
      },
      source
    );
  }

  function hoverEdge(edgeId: string, source: string) {
    cancelLeave();
    const le = ctx.edges.value.find((e) => e.id === edgeId);
    if (!le) return;
    dispatch(
      {
        type: "HOVER_EDGE",
        highlight: focusFromEdge(le, ctx.edges.value),
      },
      source
    );
  }

  function pinNode(nodeId: string, source: string) {
    cancelLeave();
    dispatch(
      {
        type: "PIN_NODE",
        highlight: focusFromNode(
          nodeId,
          ctx.productEdges.value,
          ctx.hiddenEdges.value,
          ctx.edges.value,
          ctx.nodes.value
        ),
      },
      source
    );
  }

  function pinEdge(edgeId: string, source: string) {
    cancelLeave();
    const le = ctx.edges.value.find((e) => e.id === edgeId);
    if (!le) return;
    dispatch(
      {
        type: "PIN_EDGE",
        highlight: focusFromEdge(le, ctx.edges.value),
      },
      source
    );
  }

  function scheduleLeave() {
    if (machine.value.dragging || machine.value.pinnedHighlight) return;
    cancelLeave();
    leaveTimer = setTimeout(() => {
      dispatch({ type: "POINTER_LEAVE" }, "pointer-leave");
      leaveTimer = null;
    }, LEAVE_DELAY_MS);
  }

  function clearFocus(source: string) {
    cancelLeave();
    dispatch({ type: "CLEAR" }, source);
  }

  function dragStart() {
    cancelLeave();
    dispatch({ type: "DRAG_START" }, "drag-start");
  }

  function dragEnd() {
    dispatch({ type: "DRAG_END" }, "drag-end");
  }

  function debugSummary(): string {
    const pin = isPinned.value ? " [pinned]" : "";
    return focusDebugSummary(highlight.value) + pin;
  }

  return {
    phase,
    highlight,
    isPinned,
    overlayKey,
    hoverNode,
    hoverEdge,
    pinNode,
    pinEdge,
    scheduleLeave,
    clearFocus,
    dragStart,
    dragEnd,
    debugSummary,
  };
}

export type CanvasFocusController = ReturnType<typeof useCanvasFocus>;
