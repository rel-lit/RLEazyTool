import { onLongPress, useElementHover, useEventListener } from "@vueuse/core";
import { computed, ref, toValue, watch, type MaybeRef } from "vue";
import type { InteractionTargetHandlers, UseInteractiveTargetOptions } from "./types";

type ElementRef = MaybeRef<HTMLElement | null | undefined>;

/**
 * 统一交互目标：基于 @vueuse/core，不替代原生 click/contextmenu，
 * 仅补充可订阅语义与 data-ui-* 状态属性（供样式或调试）。
 */
export function useInteractiveTarget(
  target: ElementRef,
  handlers: InteractionTargetHandlers = {},
  options: UseInteractiveTargetOptions = {}
) {
  const disabled = computed(() => toValue(options.disabled) ?? false);
  const isFocused = ref(false);
  const isPressed = ref(false);

  const isHovered = useElementHover(target, {
    delayEnter: options.hoverDelayEnter,
    delayLeave: options.hoverDelayLeave,
  });

  watch(isHovered, (hovering, prev) => {
    if (hovering === prev) return;
    handlers.onHoverChange?.(hovering);
    if (hovering) handlers.onHoverStart?.();
    else handlers.onHoverEnd?.();
  });

  watch(isFocused, (focused) => handlers.onFocusChange?.(focused));
  watch(isPressed, (pressed) => handlers.onPressChange?.(pressed));

  onLongPress(
    target,
    (event) => {
      if (disabled.value) return;
      handlers.onLongPress?.(event);
    },
    {
      delay: options.longPressDelay ?? 500,
      distanceThreshold: options.longPressDistanceThreshold ?? 10,
    }
  );

  useEventListener(target, "focus", () => {
    if (disabled.value) return;
    isFocused.value = true;
    handlers.onFocus?.();
  });

  useEventListener(target, "blur", () => {
    isFocused.value = false;
    handlers.onBlur?.();
  });

  useEventListener(target, "pointerdown", (event: PointerEvent) => {
    if (disabled.value) return;
    isPressed.value = true;
    handlers.onPressStart?.(event);
  });

  useEventListener(target, "pointerup", (event: PointerEvent) => {
    if (!isPressed.value) return;
    isPressed.value = false;
    handlers.onPressEnd?.(event);
  });

  useEventListener(target, "pointercancel", (event: PointerEvent) => {
    if (!isPressed.value) return;
    isPressed.value = false;
    handlers.onPressCancel?.(event);
  });

  useEventListener(target, "pointerleave", (event: PointerEvent) => {
    if (!isPressed.value) return;
    isPressed.value = false;
    handlers.onPressCancel?.(event);
  });

  useEventListener(target, "contextmenu", (event: MouseEvent) => {
    if (disabled.value) return;
    handlers.onSecondaryClick?.(event);
  });

  useEventListener(
    target,
    "wheel",
    (event: WheelEvent) => {
      if (disabled.value) return;
      handlers.onWheel?.(event);
    },
    { passive: true }
  );

  useEventListener(target, "auxclick", (event: MouseEvent) => {
    if (disabled.value) return;
    if (event.button !== 1) return;
    handlers.onAuxClick?.(event);
  });

  const uiStateAttrs = computed(() => {
    if (disabled.value) {
      return { "data-ui-disabled": true as const };
    }
    return {
      "data-ui-hover": isHovered.value ? true : undefined,
      "data-ui-pressed": isPressed.value ? true : undefined,
      "data-ui-focused": isFocused.value ? true : undefined,
    };
  });

  return {
    isHovered,
    isFocused,
    isPressed,
    uiStateAttrs,
  };
}
