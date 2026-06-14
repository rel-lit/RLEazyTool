import type { AppContext } from "../context";

export function wireStatus(ctx: AppContext): () => void {
  const { status } = ctx;

  const off1 = ctx.bus.on("ImportStarted", (e) => {
    status.clearWarnings();
    status.setMessage(`正在从存档「${e.saveKey}」导出进度（覆盖缓存，约 1–2 分钟）…`);
  });
  const off2 = ctx.bus.on("ImportFailed", (e) => {
    status.setMessage(e.message);
  });
  const off3 = ctx.bus.on("ProgressChanged", (e) => {
    status.setMessage(
      `已导入存档「${e.saveKey}」：${e.catalog.manufacture_items.length} 种可制造，${e.catalog.supply_items.length} 种可供给（${e.enabledCount} 条已解锁配方）`
    );
    status.setWarnings(e.warnings);
  });
  const off4 = ctx.bus.on("ProgressCleared", () => {
    status.setMessage("当前无存档进度，请先「从存档导入」");
  });
  const off5 = ctx.bus.on("SessionRefreshed", (e) => {
    if (e.status.progress_stale && e.status.active_save_key) {
      status.setWarnings([
        `存档「${e.status.active_save_key}」已在游戏中更新，当前仍使用上次导入的进度。`,
      ]);
    }
  });
  const off6 = ctx.bus.on("CatalogLoaded", (e) => {
    if (e.mode === "progress") {
      if (e.progressLoaded) {
        status.setMessage(
          `仅当前进度：${e.catalog.manufacture_items.length} 种可制造，${e.catalog.supply_items.length} 种可供给`
        );
        if (e.progressStale && e.activeSaveKey) {
          status.setWarnings([
            `存档「${e.activeSaveKey}」已在游戏中更新，当前仍使用上次导入的进度。`,
          ]);
        }
      } else {
        status.setMessage("尚未导入存档，请先「从存档导入」");
      }
    } else if (!e.hasRecipePack) {
      status.setMessage("尚无完整配方包；「从存档导入」会自动建立对应版本的数据库");
    } else {
      status.setMessage(
        `完整全配方：${e.catalog.manufacture_items.length} 种可制造，${e.catalog.supply_items.length} 种可供给`
      );
    }
  });
  const off7 = ctx.bus.on("CatalogLoadFailed", (e) => {
    status.setMessage(e.message);
  });
  const off8 = ctx.bus.on("CachePurgeStarted", () => {
    status.clearWarnings();
    status.setMessage("正在清理过时缓存…");
  });
  const off9 = ctx.bus.on("CachePurged", (e) => {
    status.setMessage(
      `已清理：${e.result.deleted_packs} 个配方包，${e.result.deleted_progress} 条存档进度`
    );
    if (e.result.legacy_files_removed.length) {
      status.setWarnings([`已删除旧 JSON：${e.result.legacy_files_removed.join("、")}`]);
    }
  });

  return () => {
    off1();
    off2();
    off3();
    off4();
    off5();
    off6();
    off7();
    off8();
    off9();
  };
}
