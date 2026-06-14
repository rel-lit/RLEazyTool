import { onUnmounted, ref, type Ref } from "vue";

const MIN_CANVAS_PX = 56;
const TOP_GAP_PX = 10;
const DEFAULT_INFO_PX = 220;

export function useInfoPanelSplit(stageRef: Ref<HTMLElement | null>) {
  const infoHeight = ref(0);
  const atMax = ref(false);
  const dragging = ref(false);
  const closeVisible = ref(false);

  let dragStartY = 0;
  let dragStartHeight = 0;

  function maxInfoHeight(): number {
    const stage = stageRef.value;
    if (!stage) return DEFAULT_INFO_PX;
    return Math.max(0, stage.clientHeight - MIN_CANVAS_PX - TOP_GAP_PX);
  }

  function clampHeight(next: number): number {
    const max = maxInfoHeight();
    const clamped = Math.min(Math.max(0, next), max);
    atMax.value = clamped >= max && max > 0;
    return clamped;
  }

  function onHandlePointerDown(event: PointerEvent): void {
    if (event.button !== 0) return;
    const target = event.currentTarget as HTMLElement;
    target.setPointerCapture(event.pointerId);
    dragging.value = true;
    closeVisible.value = false;
    dragStartY = event.clientY;
    dragStartHeight = infoHeight.value;
    event.preventDefault();
  }

  function onHandlePointerMove(event: PointerEvent): void {
    if (!dragging.value) return;
    const delta = dragStartY - event.clientY;
    infoHeight.value = clampHeight(dragStartHeight + delta);
  }

  function onHandlePointerUp(event: PointerEvent): void {
    if (!dragging.value) return;
    dragging.value = false;
    closeVisible.value = infoHeight.value > 0;
    const target = event.currentTarget as HTMLElement;
    if (target.hasPointerCapture(event.pointerId)) {
      target.releasePointerCapture(event.pointerId);
    }
  }

  function closeInfo(): void {
    infoHeight.value = 0;
    atMax.value = false;
    closeVisible.value = false;
  }

  function openInfoToDefault(): void {
    infoHeight.value = clampHeight(DEFAULT_INFO_PX);
    closeVisible.value = true;
  }

  onUnmounted(() => {
    dragging.value = false;
  });

  return {
    infoHeight,
    atMax,
    dragging,
    closeVisible,
    onHandlePointerDown,
    onHandlePointerMove,
    onHandlePointerUp,
    closeInfo,
    openInfoToDefault,
  };
}
