import { useEventListener } from "@vueuse/core";
import type { Ref } from "vue";

/** 可滚动区域：抑制空白处系统右键菜单；滚轮由原生 overflow 处理 */
export function useScrollRegion(rootRef: Ref<HTMLElement | null | undefined>): void {
  useEventListener(rootRef, "contextmenu", (event) => {
    event.preventDefault();
  });
}
