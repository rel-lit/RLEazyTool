import { useEventListener } from "@vueuse/core";
import { toRef, toValue, type MaybeRef, type Ref } from "vue";
import type { UiControlEmit } from "./events";
import { useInteractiveTarget } from "./useInteractiveTarget";

export function useUiControl(
  rootRef: Ref<HTMLButtonElement | null>,
  emit: UiControlEmit,
  options: {
    disabled: MaybeRef<boolean>;
    suppressContextMenu?: MaybeRef<boolean>;
  }
) {
  const disabled = toRef(options.disabled);
  const suppressContextMenu = toRef(() => toValue(options.suppressContextMenu) ?? false);

  const interaction = useInteractiveTarget(
    rootRef,
    {
      onLongPress: (event) => emit("longPress", event),
      onSecondaryClick: (event) => {
        if (suppressContextMenu.value) event.preventDefault();
        emit("secondary", event);
      },
      onAuxClick: (event) => emit("auxClick", event),
      onWheel: (event) => emit("wheel", event),
      onHoverChange: (hovering) => emit("hoverChange", hovering),
      onFocusChange: (focused) => emit("focusChange", focused),
      onPressChange: (pressed) => emit("pressChange", pressed),
    },
    { disabled }
  );

  useEventListener(rootRef, "click", (event: MouseEvent) => {
    if (disabled.value) return;
    emit("primary", event);
  });

  return interaction;
}
