import { onMounted, reactive, watch } from "vue";
import { createAppEventBus } from "./events";
import { bootstrapApp, loadCatalogFromApi, wireAppModules } from "./wireModules";
import { useCatalog } from "../domains/catalog/useCatalog";
import { useImportController } from "../domains/import/useImportController";
import { useLayout } from "../domains/layout/useLayout";
import { useLayoutHistory } from "../domains/layout/useLayoutHistory";
import { usePurgeController } from "../domains/purge/usePurgeController";
import { useSavePicker } from "../domains/save-picker/useSavePicker";
import { useSelection } from "../domains/selection/useSelection";
import { useSession } from "../domains/session/useSession";
import { useStatusPanel } from "../domains/status/useStatusPanel";

export function useApp() {
  const bus = createAppEventBus();

  const session = useSession(bus);
  const savePicker = useSavePicker(bus, session);
  const catalog = useCatalog(bus);
  const selection = useSelection(bus);
  const layout = useLayout(bus, selection, catalog.mode);
  const layoutHistory = useLayoutHistory(bus);
  const status = useStatusPanel(bus);
  const importCtrl = useImportController(bus, savePicker);
  const purgeCtrl = usePurgeController(bus, session, catalog);

  const modules = { bus, session, catalog, selection, layout, layoutHistory };
  wireAppModules(modules);

  watch(selection.supplyMode, () => {
    bus.emit({ type: "SelectionChanged", reason: "user-toggle" });
  });

  async function switchCatalogMode(mode: "progress" | "full"): Promise<void> {
    if (catalog.mode.value === mode) return;
    await loadCatalogFromApi(bus, catalog, mode);
  }

  onMounted(() => {
    void bootstrapApp(modules);
  });

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
    switchCatalogMode,
  });
}

export type AppContext = ReturnType<typeof useApp>;
