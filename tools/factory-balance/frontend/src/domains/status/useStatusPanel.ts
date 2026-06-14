import { ref } from "vue";
import type { AppEventBus } from "../../app/events";

export function useStatusPanel(_bus: AppEventBus) {
  const message = ref("");
  const warnings = ref<string[]>([]);

  function setMessage(text: string): void {
    message.value = text;
  }

  function setWarnings(list: string[]): void {
    warnings.value = list;
  }

  function clearWarnings(): void {
    warnings.value = [];
  }

  return {
    message,
    warnings,
    setMessage,
    setWarnings,
    clearWarnings,
  };
}

export type StatusModule = ReturnType<typeof useStatusPanel>;
