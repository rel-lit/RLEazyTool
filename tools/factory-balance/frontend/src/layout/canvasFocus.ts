import { ref } from "vue";

/** 强制 Vue Flow 内自定义节点/边在 focus 变化时重算 computed */
export const focusTick = ref(0);

export function bumpFocusTick(): void {
  focusTick.value += 1;
}
