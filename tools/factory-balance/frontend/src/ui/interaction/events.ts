/** UiControl 标准 emit（业务层只订阅语义事件，不绑 raw DOM） */
export type UiControlEmit = {
  (event: "primary", payload: MouseEvent): void;
  (event: "secondary", payload: MouseEvent): void;
  (event: "longPress", payload: PointerEvent): void;
  (event: "auxClick", payload: MouseEvent): void;
  (event: "wheel", payload: WheelEvent): void;
  (event: "hoverChange", payload: boolean): void;
  (event: "focusChange", payload: boolean): void;
  (event: "pressChange", payload: boolean): void;
};
