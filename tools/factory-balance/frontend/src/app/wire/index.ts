import type { AppActions } from "../actions/createAppActions";
import type { AppContext, CanvasLayoutHooks } from "../context";
import { wireCatalog } from "./wireCatalog";
import { wireHistory } from "./wireHistory";
import { wireItemList } from "./wireItemList";
import { wireLayout } from "./wireLayout";
import { wireProgress } from "./wireProgress";
import { wireSavePicker } from "./wireSavePicker";
import { wireSelection } from "./wireSelection";
import { wireStatus } from "./wireStatus";

export function wireApp(ctx: AppContext, actions: AppActions): () => void {
  const cleanups = [
    wireProgress(ctx),
    wireCatalog(ctx),
    wireSelection(ctx),
    wireLayout(ctx, actions),
    wireItemList(ctx, actions),
    wireStatus(ctx),
    wireSavePicker(ctx),
    wireHistory(ctx),
  ];
  return () => {
    for (const off of cleanups) off();
  };
}

export { bootstrapApp } from "./wireProgress";
