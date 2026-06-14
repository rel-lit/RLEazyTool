import type { AppContext } from "../context";

export function wireSavePicker(ctx: AppContext): () => void {
  const off1 = ctx.bus.on("SessionRefreshed", () => {
    ctx.savePicker.initDefault();
  });
  const off2 = ctx.bus.on("ProgressChanged", (e) => {
    ctx.savePicker.syncActiveSave(e.saveKey);
  });
  return () => {
    off1();
    off2();
  };
}
