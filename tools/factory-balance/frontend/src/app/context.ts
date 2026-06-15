import type { AppEventBus } from "./events";
import type { CatalogModule } from "../domains/catalog/useCatalog";
import type { ItemListBundle } from "../domains/item-list/itemListBundle";
import type { LayoutInspectionModule } from "../domains/layout-inspection";
import type { LayoutModule } from "../domains/layout/useLayout";
import type { LayoutHistoryModule } from "../domains/layout/useLayoutHistory";
import type { LayoutPersistence } from "../domains/layout/layoutPersistence";
import type { ListLayoutMarkModule } from "../domains/list-layout-mark";
import type { SelectionModule } from "../domains/selection/useSelection";
import type { useSession } from "../domains/session/useSession";
import type { StatusModule } from "../domains/status/useStatusPanel";
import type { SavePickerModule } from "../domains/save-picker/useSavePicker";

export interface CanvasLayoutHooks {
  prepareForNewLayout: () => void;
}

export interface AppContext {
  bus: AppEventBus;
  session: ReturnType<typeof useSession>;
  catalog: CatalogModule;
  selection: SelectionModule;
  layout: LayoutModule;
  layoutInspection: LayoutInspectionModule;
  layoutHistory: LayoutHistoryModule;
  persistence: LayoutPersistence;
  status: StatusModule;
  savePicker: SavePickerModule;
  itemList: ItemListBundle;
  listLayoutMark: ListLayoutMarkModule;
  canvasLayoutHooks: CanvasLayoutHooks;
}
