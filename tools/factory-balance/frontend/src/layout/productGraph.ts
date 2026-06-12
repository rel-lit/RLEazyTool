import type { LayoutEdge } from "../api/client";

export interface ProductGraph {
  /** 物料流 from→to（等级递增，朝向终端） */
  forward: Map<string, { to: string; edgeId: string }[]>;
  /** 依赖方向 to→from（朝向纯粹原料，终端为根的子树方向） */
  reverse: Map<string, { from: string; edgeId: string }[]>;
  edgesById: Map<string, LayoutEdge>;
}

export function edgeKey(from: string, to: string, item: string): string {
  return `${from}\0${to}\0${item}`;
}

export function buildProductGraph(productEdges: LayoutEdge[]): ProductGraph {
  const forward = new Map<string, { to: string; edgeId: string }[]>();
  const reverse = new Map<string, { from: string; edgeId: string }[]>();
  const edgesById = new Map<string, LayoutEdge>();

  for (const e of productEdges) {
    edgesById.set(e.id, e);
    const fwd = forward.get(e.from) ?? [];
    fwd.push({ to: e.to, edgeId: e.id });
    forward.set(e.from, fwd);
    const rev = reverse.get(e.to) ?? [];
    rev.push({ from: e.from, edgeId: e.id });
    reverse.set(e.to, rev);
  }

  return { forward, reverse, edgesById };
}

/**
 * 终端为根、原料为叶：从 nodeId 沿依赖方向（朝向更低等级/原料）扩展子树。
 */
export function dependencySubtree(
  graph: ProductGraph,
  nodeId: string
): { nodeIds: Set<string>; productEdgeIds: Set<string> } {
  const nodeIds = new Set<string>([nodeId]);
  const productEdgeIds = new Set<string>();
  const queue = [nodeId];

  while (queue.length > 0) {
    const id = queue.shift()!;
    for (const { from, edgeId } of graph.reverse.get(id) ?? []) {
      productEdgeIds.add(edgeId);
      if (!nodeIds.has(from)) {
        nodeIds.add(from);
        queue.push(from);
      }
    }
  }

  return { nodeIds, productEdgeIds };
}

/** 朝向终端/更高等级：仅直接相连的一跳 */
export function directDownstreamHop(
  graph: ProductGraph,
  nodeId: string
): { nodeIds: Set<string>; productEdgeIds: Set<string> } {
  const nodeIds = new Set<string>();
  const productEdgeIds = new Set<string>();

  for (const { to, edgeId } of graph.forward.get(nodeId) ?? []) {
    productEdgeIds.add(edgeId);
    nodeIds.add(to);
  }

  return { nodeIds, productEdgeIds };
}

export function indexEdgesByKey(edges: LayoutEdge[]): Map<string, LayoutEdge> {
  const map = new Map<string, LayoutEdge>();
  for (const e of edges) {
    map.set(edgeKey(e.from, e.to, e.item), e);
  }
  return map;
}

export function indexBeltIds(layoutEdges: LayoutEdge[]): Map<string, string> {
  const map = new Map<string, string>();
  for (const e of layoutEdges) {
    if (e.type === "belt") {
      map.set(edgeKey(e.from, e.to, e.item), e.id);
    }
  }
  return map;
}

/** 产物边 → 可见 belt 或 hidden（SBTO 替代的反向树实线） */
export function mapProductEdgesToLayout(
  productEdgeIds: Set<string>,
  graph: ProductGraph,
  beltIds: Map<string, string>,
  hiddenByKey: Map<string, LayoutEdge>
): { beltEdgeIds: Set<string>; hiddenEdgeIds: Set<string> } {
  const beltEdgeIds = new Set<string>();
  const hiddenEdgeIds = new Set<string>();

  for (const pid of productEdgeIds) {
    const pe = graph.edgesById.get(pid);
    if (!pe) continue;
    const key = edgeKey(pe.from, pe.to, pe.item);
    const beltId = beltIds.get(key);
    if (beltId) {
      beltEdgeIds.add(beltId);
      continue;
    }
    const hidden = hiddenByKey.get(key);
    if (hidden) {
      hiddenEdgeIds.add(hidden.id);
    }
  }

  return { beltEdgeIds, hiddenEdgeIds };
}

/** 合并节点：从该节点出发、被 SBTO 隐藏的全部反向树实线 */
export function mergeNodeHiddenFanout(
  nodeId: string,
  hiddenEdges: LayoutEdge[]
): { nodeIds: Set<string>; hiddenEdgeIds: Set<string> } {
  const nodeIds = new Set<string>();
  const hiddenEdgeIds = new Set<string>();

  for (const e of hiddenEdges) {
    if (e.from === nodeId) {
      hiddenEdgeIds.add(e.id);
      nodeIds.add(e.to);
    }
  }

  return { nodeIds, hiddenEdgeIds };
}

export function isMergeNode(nodeId: string, hiddenEdges: LayoutEdge[]): boolean {
  return hiddenEdges.some((e) => e.from === nodeId);
}

export function sbtoItemsFromNode(
  nodeId: string,
  hiddenEdges: LayoutEdge[]
): Set<string> {
  const items = new Set<string>();
  for (const e of hiddenEdges) {
    if (e.from === nodeId) {
      items.add(e.item);
    }
  }
  return items;
}
