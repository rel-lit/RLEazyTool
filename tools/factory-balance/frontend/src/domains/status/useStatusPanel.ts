import { ref } from "vue";
import type { AppEventBus } from "../../app/events";

export function useStatusPanel(bus: AppEventBus) {
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

  bus.on("ImportStarted", (e) => {
    clearWarnings();
    message.value = `正在从存档「${e.saveKey}」导出进度（覆盖缓存，约 1–2 分钟）…`;
  });

  bus.on("ImportFailed", (e) => {
    message.value = e.message;
  });

  bus.on("ProgressChanged", (e) => {
    message.value = `已导入存档「${e.saveKey}」：${e.catalog.manufacture_items.length} 种可制造，${e.catalog.supply_items.length} 种可供给（${e.enabledCount} 条已解锁配方）`;
    warnings.value = e.warnings;
  });

  bus.on("ProgressCleared", () => {
    message.value = "当前无存档进度，请先「从存档导入」";
  });

  bus.on("SessionRefreshed", (e) => {
    if (e.status.progress_stale && e.status.active_save_key) {
      warnings.value = [
        `存档「${e.status.active_save_key}」已在游戏中更新，当前仍使用上次导入的进度。`,
      ];
    }
  });

  bus.on("CatalogLoaded", (e) => {
    if (e.mode === "progress") {
      if (e.progressLoaded) {
        message.value = `仅当前进度：${e.catalog.manufacture_items.length} 种可制造，${e.catalog.supply_items.length} 种可供给`;
        if (e.progressStale && e.activeSaveKey) {
          warnings.value = [
            `存档「${e.activeSaveKey}」已在游戏中更新，当前仍使用上次导入的进度。`,
          ];
        }
      } else {
        message.value = "尚未导入存档，请先「从存档导入」";
      }
    } else if (!e.hasRecipePack) {
      message.value = "尚无完整配方包；「从存档导入」会自动建立对应版本的数据库";
    } else {
      message.value = `完整全配方：${e.catalog.manufacture_items.length} 种可制造，${e.catalog.supply_items.length} 种可供给`;
    }
  });

  bus.on("CatalogLoadFailed", (e) => {
    message.value = e.message;
  });

  bus.on("CachePurgeStarted", () => {
    clearWarnings();
    message.value = "正在清理过时缓存…";
  });

  bus.on("CachePurged", (e) => {
    message.value = `已清理：${e.result.deleted_packs} 个配方包，${e.result.deleted_progress} 条存档进度`;
    if (e.result.legacy_files_removed.length) {
      warnings.value = [`已删除旧 JSON：${e.result.legacy_files_removed.join("、")}`];
    }
  });

  bus.on("LayoutInvalidated", () => {
    if (message.value && !message.value.includes("选项已变")) {
      // 保留 catalog/import 文案，stale 由 layout 模块 UI 展示
    }
  });

  bus.on("LayoutComputeFailed", (e) => {
    // error 在 layout 模块；此处可选追加
    if (!message.value.includes(e.message)) {
      // 不覆盖 import/catalog 主文案
    }
  });

  return {
    message,
    warnings,
    setMessage,
    setWarnings,
    clearWarnings,
  };
}

export type StatusModule = ReturnType<typeof useStatusPanel>;
