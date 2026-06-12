import { ref } from "vue";
import type { SaveInfo } from "../../api/client";
import type { AppEventBus } from "../../app/events";
import type { useSession } from "../session/useSession";

export function useSavePicker(bus: AppEventBus, session: ReturnType<typeof useSession>) {
  const selectedSave = ref("");

  function initDefault(): void {
    if (selectedSave.value) return;
    const saves = session.saves.value;
    const last = saves.find((s) => s.is_last_played);
    selectedSave.value =
      last?.name ??
      session.status.value?.last_played_save ??
      saves[0]?.name ??
      "";
  }

  function syncAfterSessionRefresh(): void {
    initDefault();
  }

  function syncActiveSave(saveKey: string): void {
    selectedSave.value = saveKey;
  }

  bus.on("SessionRefreshed", () => {
    syncAfterSessionRefresh();
  });

  bus.on("ProgressChanged", (e) => {
    syncActiveSave(e.saveKey);
  });

  return {
    selectedSave,
    initDefault,
    syncActiveSave,
  };
}

export type SavePickerModule = ReturnType<typeof useSavePicker>;
