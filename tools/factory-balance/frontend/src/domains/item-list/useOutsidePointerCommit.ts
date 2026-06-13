import { onMounted, onUnmounted } from "vue";

/**
 * 区外 pointer 提交（对齐 Radix DismissableLayer / onPointerDownOutside）：
 * document capture 阶段监听，目标不在 region 内则回调。
 *
 * 须在面板级注册**单例**，勿在每个列表区重复挂载，否则 inactive 区也会误触发 commit。
 */
export function useOutsidePointerCommit(
  getRegionRoot: () => HTMLElement | null,
  onCommit: () => void,
  /** 命中时不触发 commit（如 tab 栏由 switchTab 自行处理） */
  isIgnoredTarget?: (target: Node) => boolean
): void {
  function onDocumentPointerDown(event: PointerEvent): void {
    const root = getRegionRoot();
    if (!root) return;
    const target = event.target;
    if (!(target instanceof Node)) return;
    if (root.contains(target)) return;
    if (isIgnoredTarget?.(target)) return;
    onCommit();
  }

  onMounted(() => {
    document.addEventListener("pointerdown", onDocumentPointerDown, true);
  });

  onUnmounted(() => {
    document.removeEventListener("pointerdown", onDocumentPointerDown, true);
  });
}
