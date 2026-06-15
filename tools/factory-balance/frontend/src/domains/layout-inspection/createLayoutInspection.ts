import { computed, ref, shallowRef } from "vue";
import type { LayoutRequest, LayoutResponse } from "../../api/client";
import type { FocusHighlight } from "../../layout/focus/focusModel";
import type { CanvasRegionTarget } from "../../ui/interaction/canvas/types";
import { usePinHighlight } from "../../ui/interaction/usePinHighlight";
import { projectFocusView } from "./focusProjection";
import { resolveInspectionPanel } from "./resolveInspectionPanel";
import type { InspectionTarget } from "./types";

/**
 * 画布检视会话：hover/pin 高亮 + primary 选中 + 信息栏模型。
 * 不含 Vue Flow；canvas 层注入 pin 与 resolver。
 */
export function createLayoutInspection() {
  const pin = usePinHighlight<FocusHighlight>();
  const layoutRef = shallowRef<LayoutResponse | null>(null);
  const requestRef = shallowRef<LayoutRequest | null>(null);
  const inspectionTarget = ref<InspectionTarget | null>(null);
  const revision = ref(0);

  function bump(): void {
    revision.value += 1;
  }

  function setLayout(layout: LayoutResponse | null, request?: LayoutRequest | null): void {
    layoutRef.value = layout;
    if (layout === null) {
      requestRef.value = null;
    } else if (request !== undefined) {
      requestRef.value = request;
    }
    bump();
  }

  function clear(): void {
    pin.clear();
    inspectionTarget.value = null;
    bump();
  }

  const selectedEdgeId = computed(() =>
    inspectionTarget.value?.kind === "edge" ? inspectionTarget.value.id : null
  );

  const focusView = computed(() => {
    void revision.value;
    return projectFocusView(pin.highlight.value, pin.isPinned.value);
  });

  const panelModel = computed(() => {
    void revision.value;
    return resolveInspectionPanel(
      inspectionTarget.value,
      layoutRef.value,
      focusView.value,
      requestRef.value
    );
  });

  function handlePrimary(target: CanvasRegionTarget): void {
    if (target.kind === "edge") {
      inspectionTarget.value = { kind: "edge", id: target.id };
      bump();
      return;
    }
    if (target.kind === "node") {
      inspectionTarget.value = { kind: "node", id: target.id };
      bump();
      return;
    }
    clear();
  }

  return {
    revision,
    pin,
    layoutRef,
    requestRef,
    inspectionTarget,
    selectedEdgeId,
    focusView,
    panelModel,
    setLayout,
    clear,
    handlePrimary,
  };
}

export type LayoutInspectionModule = ReturnType<typeof createLayoutInspection>;
