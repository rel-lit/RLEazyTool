import type { MaybeRef } from "vue";

/** 底层可订阅的交互语义（业务按需选用，不强制） */
export type InteractionSemantic =
  | "primary-click"
  | "secondary-click"
  | "long-press"
  | "hover-start"
  | "hover-end"
  | "focus"
  | "blur"
  | "press-start"
  | "press-end"
  | "press-cancel"
  | "wheel"
  | "aux-click";

export interface InteractionTargetHandlers {
  onHoverStart?: () => void;
  onHoverEnd?: () => void;
  onHoverChange?: (hovering: boolean) => void;
  onFocus?: () => void;
  onBlur?: () => void;
  onFocusChange?: (focused: boolean) => void;
  onPressStart?: (event: PointerEvent) => void;
  onPressEnd?: (event: PointerEvent) => void;
  onPressCancel?: (event: PointerEvent) => void;
  onPressChange?: (pressed: boolean) => void;
  onLongPress?: (event: PointerEvent) => void;
  /** 右键 / contextmenu */
  onSecondaryClick?: (event: MouseEvent) => void;
  onWheel?: (event: WheelEvent) => void;
  /** 中键 */
  onAuxClick?: (event: MouseEvent) => void;
}

export interface UseInteractiveTargetOptions {
  disabled?: MaybeRef<boolean>;
  longPressDelay?: number;
  longPressDistanceThreshold?: number | false;
  hoverDelayEnter?: number;
  hoverDelayLeave?: number;
}
