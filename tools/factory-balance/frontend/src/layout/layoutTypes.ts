/** 与后端 PrimaryDirection / layout_direction 一致 */
export type LayoutDirection = "left-to-right" | "top-to-bottom";

export const DEFAULT_LAYOUT_DIRECTION: LayoutDirection = "left-to-right";

export type FactoryNodeKind = "supply" | "producer" | "sink" | "buffer_placeholder";
