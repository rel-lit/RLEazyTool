import { toRef, type Ref } from "vue";
import { useInteractiveTarget } from "./useInteractiveTarget";

/** UiButton / UiChip 共用的 emit 桥接，业务仍可直接 @click / @contextmenu */
export function useUiControlInteraction(
  rootRef: Ref<HTMLButtonElement | null>,
  emit: {
    (event: "longPress", payload: PointerEvent): void;
    (event: "secondaryClick", payload: MouseEvent): void;
    (event: "auxClick", payload: MouseEvent): void;
    (event: "wheel", payload: WheelEvent): void;
    (event: "hoverChange", payload: boolean): void;
    (event: "focusChange", payload: boolean): void;
    (event: "pressChange", payload: boolean): void;
  },
  disabled: Ref<boolean> | { value: boolean }
) {
  return useInteractiveTarget(
    rootRef,
    {
      onLongPress: (event) => emit("longPress", event),
      onSecondaryClick: (event) => emit("secondaryClick", event),
      onAuxClick: (event) => emit("auxClick", event),
      onWheel: (event) => emit("wheel", event),
      onHoverChange: (hovering) => emit("hoverChange", hovering),
      onFocusChange: (focused) => emit("focusChange", focused),
      onPressChange: (pressed) => emit("pressChange", pressed),
    },
    { disabled: toRef(disabled) }
  );
}
