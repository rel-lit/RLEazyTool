import { ref } from "vue";
import { loadProgress } from "../../api/client";
import type { AppEventBus } from "../../app/events";
import type { SavePickerModule } from "../save-picker/useSavePicker";

export function useImportController(bus: AppEventBus, savePicker: SavePickerModule) {
  const loading = ref(false);

  async function importFromSave(): Promise<void> {
    const saveKey = savePicker.selectedSave.value;
    if (!saveKey) {
      bus.emit({ type: "ImportFailed", message: "请选择存档" });
      return;
    }

    loading.value = true;
    bus.emit({ type: "ImportStarted", saveKey });

    try {
      const res = await loadProgress(saveKey, true);
      if (!res.ok || !res.save) {
        bus.emit({ type: "ImportFailed", message: "导入失败" });
        return;
      }

      bus.emit({
        type: "ProgressChanged",
        saveKey: res.save,
        catalog: {
          manufacture_items: res.manufacture_items ?? res.craftable_items,
          supply_items: res.supply_items ?? [],
        },
        warnings: res.warnings,
        enabledCount: res.enabled_recipe_count,
        progressStale: res.progress_stale,
      });
    } catch (e: unknown) {
      bus.emit({
        type: "ImportFailed",
        message: e instanceof Error ? e.message : "从存档导入失败",
      });
    } finally {
      loading.value = false;
    }
  }

  return {
    loading,
    importFromSave,
  };
}

export type ImportModule = ReturnType<typeof useImportController>;
