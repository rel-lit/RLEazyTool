import { getBezierPath, Position, type Position as FlowPosition } from "@vue-flow/core";

function calculateControlOffset(distance: number, curvature: number): number {
  if (distance >= 0) return 0.5 * distance;
  return curvature * 25 * Math.sqrt(-distance);
}

function controlWithCurvature(
  pos: FlowPosition,
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  c: number
): [number, number] {
  switch (pos) {
    case Position.Left:
      return [x1 - calculateControlOffset(x1 - x2, c), y1];
    case Position.Right:
      return [x1 + calculateControlOffset(x2 - x1, c), y1];
    case Position.Top:
      return [x1, y1 - calculateControlOffset(y1 - y2, c)];
    case Position.Bottom:
      return [x1, y1 + calculateControlOffset(y2 - y1, c)];
    default:
      return [x1, y1];
  }
}

function bezierCenter(
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
  scX: number,
  scY: number,
  tcX: number,
  tcY: number
): [number, number] {
  const cx =
    sourceX * 0.125 + scX * 0.375 + tcX * 0.375 + targetX * 0.125;
  const cy =
    sourceY * 0.125 + scY * 0.375 + tcY * 0.375 + targetY * 0.125;
  return [cx, cy];
}

/**
 * 端点固定在 handle 上，仅沿法向偏移控制点，使平行线在路径中段分开。
 */
export function bezierPathWithGap(params: {
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  sourcePosition: FlowPosition;
  targetPosition: FlowPosition;
  curvature?: number;
  gapPx?: number;
  /** 无向节点对统一法向；与 gapPx 相乘后偏移控制点，避免反向边同侧重叠 */
  gapNx?: number;
  gapNy?: number;
}): [string, number, number] {
  const gap = params.gapPx ?? 0;
  const curvature = params.curvature ?? 0.25;

  if (gap === 0) {
    const [path, lx, ly] = getBezierPath({
      sourceX: params.sourceX,
      sourceY: params.sourceY,
      sourcePosition: params.sourcePosition,
      targetX: params.targetX,
      targetY: params.targetY,
      targetPosition: params.targetPosition,
      curvature,
    });
    return [path, lx, ly];
  }

  const { sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition } =
    params;

  const [scX, scY] = controlWithCurvature(
    sourcePosition,
    sourceX,
    sourceY,
    targetX,
    targetY,
    curvature
  );
  const [tcX, tcY] = controlWithCurvature(
    targetPosition,
    targetX,
    targetY,
    sourceX,
    sourceY,
    curvature
  );

  let ox: number;
  let oy: number;
  if (params.gapNx != null && params.gapNy != null) {
    ox = params.gapNx * gap;
    oy = params.gapNy * gap;
  } else {
    const dx = targetX - sourceX;
    const dy = targetY - sourceY;
    const len = Math.hypot(dx, dy) || 1;
    ox = (-dy / len) * gap;
    oy = (dx / len) * gap;
  }

  const path = `M${sourceX},${sourceY} C${scX + ox},${scY + oy} ${tcX + ox},${tcY + oy} ${targetX},${targetY}`;
  const [lx, ly] = bezierCenter(
    sourceX,
    sourceY,
    targetX,
    targetY,
    scX + ox,
    scY + oy,
    tcX + ox,
    tcY + oy
  );
  return [path, lx, ly];
}
