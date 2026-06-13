import { onClickOutside } from "@vueuse/core";
import { shallowRef, watchEffect } from "vue";

/**
 * 区域外 pointer 交互（VueUse onClickOutside，capture）。
 * 用于列表 session commit、popover dismiss 等，勿在 domain 重复实现 document 监听。
 */
export function useRegionOutside(
  getRoot: () => HTMLElement | null | undefined,
  onOutside: () => void,
  options?: {
    ignore?: (target: EventTarget | null) => boolean;
  }
): void {
  const root = shallowRef<HTMLElement | null>(null);

  watchEffect(() => {
    root.value = getRoot() ?? null;
  });

  onClickOutside(
    root,
    (event) => {
      if (options?.ignore?.(event.target)) return;
      onOutside();
    },
    { capture: true }
  );
}
