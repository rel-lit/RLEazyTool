import { onMounted, onUnmounted, provide, reactive, ref, type InjectionKey } from "vue";
import { createAppEventBus } from "./events";
import { createAppActions, type AppActions } from "./actions/createAppActions";
import type { AppContext, CanvasLayoutHooks } from "./context";
import { bootstrapApp, wireApp } from "./wire";
import { useCatalog } from "../domains/catalog/useCatalog";
import { useImportController } from "../domains/import/useImportController";
import { useLayout } from "../domains/layout/useLayout";
import { createLayoutPersistence } from "../domains/layout/layoutPersistence";
import { useLayoutHistory } from "../domains/layout/useLayoutHistory";
import { usePurgeController } from "../domains/purge/usePurgeController";
import { useSavePicker } from "../domains/save-picker/useSavePicker";
import { useSelection } from "../domains/selection/useSelection";
import { useSession } from "../domains/session/useSession";
import { useStatusPanel } from "../domains/status/useStatusPanel";
import { createItemListBundle, type ItemListBundle } from "../domains/item-list/itemListBundle";
import { createListLayoutMark, type ListLayoutMarkModule } from "../domains/list-layout-mark";
import { readCanvasNodePositions } from "../layout/layoutCanvasBridge";
import { loadCatalogFromApi } from "../domains/catalog/catalogService";
import type { LayoutRequest } from "../api/client";

export const appActionsKey: InjectionKey<AppActions> = Symbol("appActions");
export const itemListKey: InjectionKey<ItemListBundle> = Symbol("itemList");
export const listLayoutMarkKey: InjectionKey<ListLayoutMarkModule> = Symbol("listLayoutMark");
export const canvasLayoutHooksKey: InjectionKey<CanvasLayoutHooks> = Symbol("canvasLayoutHooks");

export function useApp() {
  const bus = createAppEventBus();

  const session = useSession(bus);
  const catalog = useCatalog();
  const selection = useSelection(bus);
  const status = useStatusPanel(bus);
  const savePicker = useSavePicker(session);
  const itemList = createItemListBundle();
  const listLayoutMark = createListLayoutMark();

  let layoutModule: ReturnType<typeof useLayout> | undefined;
  const boundRequestRef = ref<LayoutRequest | null>(null);

  const persistence = createLayoutPersistence({
    bus,
    getLayout: () => layoutModule?.layout.value ?? null,
    getBoundRequest: () => boundRequestRef.value,
    readCanvasPositions: readCanvasNodePositions,
  });

  layoutModule = useLayout(bus, selection, catalog.mode, persistence, boundRequestRef);
  const layout = layoutModule;

  const layoutHistory = useLayoutHistory(bus, persistence);
  const importCtrl = useImportController(bus, savePicker);
  const purgeCtrl = usePurgeController(bus, session, catalog);

  const canvasHooks: CanvasLayoutHooks = {
    prepareForNewLayout: () => {},
  };

  const ctx: AppContext = {
    bus,
    session,
    catalog,
    selection,
    layout,
    layoutHistory,
    persistence,
    status,
    savePicker,
    itemList,
    listLayoutMark,
    canvasLayoutHooks: canvasHooks,
  };

  const actions = createAppActions(ctx);

  let unwired: (() => void) | null = null;

  async function switchCatalogMode(mode: "progress" | "full"): Promise<void> {
    if (catalog.mode.value === mode) return;
    await loadCatalogFromApi(bus, catalog, mode);
  }

  onMounted(() => {
    persistence.installPageLeaveHook();
    unwired = wireApp(ctx, actions);
    actions.syncItemListsFromCatalog();
    void bootstrapApp(ctx);
  });

  onUnmounted(() => {
    unwired?.();
  });

  provide(appActionsKey, actions);
  provide(itemListKey, itemList);
  provide(listLayoutMarkKey, listLayoutMark);
  provide(canvasLayoutHooksKey, canvasHooks);

  return reactive({
    bus,
    session,
    savePicker,
    catalog,
    selection,
    layout,
    layoutHistory,
    status,
    importCtrl,
    purgeCtrl,
    itemList,
    listLayoutMark,
    actions,
    switchCatalogMode,
  });
}

export type AppShell = ReturnType<typeof useApp>;
