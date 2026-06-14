import { computed, ref } from "vue";
import {
  effectivePinHighlight,
  initialPinHighlightState,
  pinHighlightReducer,
  type PinHighlightState,
} from "./pinHighlightMachine";

const DEFAULT_LEAVE_DELAY_MS = 120;

export interface UsePinHighlightOptions {
  leaveDelayMs?: number;
}

/**
 * 区内 hover / pin 高亮控制器。
 * 不含领域数据解析——由上层 region（canvas、future list focus 等）注入 highlight 对象。
 */
export function usePinHighlight<T>(options: UsePinHighlightOptions = {}) {
  const leaveDelayMs = options.leaveDelayMs ?? DEFAULT_LEAVE_DELAY_MS;
  const machine = ref<PinHighlightState<T>>({
    ...initialPinHighlightState,
    hoverHighlight: null,
    pinnedHighlight: null,
  });
  let leaveTimer: ReturnType<typeof setTimeout> | null = null;

  const highlight = computed<T | null>(() => effectivePinHighlight(machine.value));
  const isPinned = computed(() => machine.value.pinnedHighlight != null);
  const dragging = computed(() => machine.value.dragging);

  function cancelLeave(): void {
    if (leaveTimer) {
      clearTimeout(leaveTimer);
      leaveTimer = null;
    }
  }

  function dispatch(action: Parameters<typeof pinHighlightReducer<T>>[1]): void {
    if (machine.value.dragging && action.type !== "DRAG_END") return;
    machine.value = pinHighlightReducer(machine.value, action);
  }

  function hover(next: T): void {
    cancelLeave();
    dispatch({ type: "HOVER", highlight: next });
  }

  function pin(next: T): void {
    cancelLeave();
    dispatch({ type: "PIN", highlight: next });
  }

  function scheduleLeave(): void {
    if (machine.value.dragging || machine.value.pinnedHighlight) return;
    cancelLeave();
    leaveTimer = setTimeout(() => {
      dispatch({ type: "POINTER_LEAVE" });
      leaveTimer = null;
    }, leaveDelayMs);
  }

  function clear(): void {
    cancelLeave();
    dispatch({ type: "CLEAR" });
  }

  function dragStart(): void {
    cancelLeave();
    dispatch({ type: "DRAG_START" });
  }

  function dragEnd(): void {
    dispatch({ type: "DRAG_END" });
  }

  return {
    highlight,
    isPinned,
    dragging,
    hover,
    pin,
    scheduleLeave,
    clear,
    dragStart,
    dragEnd,
  };
}

export type PinHighlightController<T> = ReturnType<typeof usePinHighlight<T>>;
