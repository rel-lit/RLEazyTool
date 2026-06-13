import { useEventListener, useFocusWithin } from "@vueuse/core";
import { watch, type Ref } from "vue";

export interface UseScrollRegionOptions {
  /** 焦点离开滚动区时回到顶部，默认 true */
  resetOnBlur?: boolean;
}

/** 可滚动区域：抑制空白处系统右键菜单；失焦/离开时 scrollTop 归零 */
export function useScrollRegion(
  rootRef: Ref<HTMLElement | null | undefined>,
  options: UseScrollRegionOptions = {}
) {
  const resetOnBlur = options.resetOnBlur ?? true;

  useEventListener(rootRef, "contextmenu", (event) => {
    event.preventDefault();
  });

  function resetScroll(): void {
    const el = rootRef.value;
    if (el) el.scrollTop = 0;
  }

  if (resetOnBlur) {
    const focusedWithin = useFocusWithin(rootRef);
    watch(focusedWithin, (focused, wasFocused) => {
      if (wasFocused && !focused) resetScroll();
    });
  }

  return { resetScroll };
}
