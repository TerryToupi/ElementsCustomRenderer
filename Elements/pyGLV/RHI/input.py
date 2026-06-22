from __future__ import annotations

from enum import Enum


class Key(Enum):
    UNKNOWN = "unknown"

    A = "a"
    B = "b"
    C = "c"
    D = "d"
    E = "e"
    F = "f"
    G = "g"
    H = "h"
    I = "i"
    J = "j"
    K = "k"
    L = "l"
    M = "m"
    N = "n"
    O = "o"
    P = "p"
    Q = "q"
    R = "r"
    S = "s"
    T = "t"
    U = "u"
    V = "v"
    W = "w"
    X = "x"
    Y = "y"
    Z = "z"

    NUM_0 = "0"
    NUM_1 = "1"
    NUM_2 = "2"
    NUM_3 = "3"
    NUM_4 = "4"
    NUM_5 = "5"
    NUM_6 = "6"
    NUM_7 = "7"
    NUM_8 = "8"
    NUM_9 = "9"

    ESCAPE = "escape"
    ENTER = "enter"
    SPACE = "space"
    BACKSPACE = "backspace"
    TAB = "tab"
    SHIFT = "shift"
    CONTROL = "control"
    ALT = "alt"

    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"
    ARROW_LEFT = "left"
    ARROW_RIGHT = "right"
    ARROW_UP = "up"
    ARROW_DOWN = "down"

    F1 = "f1"
    F2 = "f2"
    F3 = "f3"
    F4 = "f4"
    F5 = "f5"
    F6 = "f6"
    F7 = "f7"
    F8 = "f8"
    F9 = "f9"
    F10 = "f10"
    F11 = "f11"
    F12 = "f12"


class MouseButton(Enum):
    UNKNOWN = "unknown"
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"
    X1 = "x1"
    X2 = "x2"


class InputState:
    def __init__(self) -> None:
        self._keys_down: set[Key] = set()
        self._keys_pressed: set[Key] = set()
        self._keys_released: set[Key] = set()
        self._mouse_buttons_down: set[MouseButton] = set()
        self._mouse_buttons_pressed: set[MouseButton] = set()
        self._mouse_buttons_released: set[MouseButton] = set()
        self.mouse_position: tuple[float, float] = (0.0, 0.0)
        self.mouse_delta: tuple[float, float] = (0.0, 0.0)
        self.mouse_wheel: tuple[float, float] = (0.0, 0.0)

    def begin_frame(self) -> None:
        self._keys_pressed.clear()
        self._keys_released.clear()
        self._mouse_buttons_pressed.clear()
        self._mouse_buttons_released.clear()
        self.mouse_delta = (0.0, 0.0)
        self.mouse_wheel = (0.0, 0.0)

    def press_key(self, key: Key, repeat: bool = False) -> None:
        if key is Key.UNKNOWN:
            return
        if key not in self._keys_down and not repeat:
            self._keys_pressed.add(key)
        self._keys_down.add(key)

    def release_key(self, key: Key) -> None:
        if key is Key.UNKNOWN:
            return
        if key in self._keys_down:
            self._keys_released.add(key)
        self._keys_down.discard(key)

    def move_mouse(self, x: float, y: float, dx: float, dy: float) -> None:
        self.mouse_position = (x, y)
        old_dx, old_dy = self.mouse_delta
        self.mouse_delta = (old_dx + dx, old_dy + dy)

    def press_mouse_button(self, button: MouseButton, x: float, y: float) -> None:
        if button is MouseButton.UNKNOWN:
            return
        self.mouse_position = (x, y)
        if button not in self._mouse_buttons_down:
            self._mouse_buttons_pressed.add(button)
        self._mouse_buttons_down.add(button)

    def release_mouse_button(self, button: MouseButton, x: float, y: float) -> None:
        if button is MouseButton.UNKNOWN:
            return
        self.mouse_position = (x, y)
        if button in self._mouse_buttons_down:
            self._mouse_buttons_released.add(button)
        self._mouse_buttons_down.discard(button)

    def scroll_mouse(self, x: float, y: float) -> None:
        old_x, old_y = self.mouse_wheel
        self.mouse_wheel = (old_x + x, old_y + y)

    def is_key_down(self, key: Key) -> bool:
        return key in self._keys_down

    def was_key_pressed(self, key: Key) -> bool:
        return key in self._keys_pressed

    def was_key_released(self, key: Key) -> bool:
        return key in self._keys_released

    def is_mouse_button_down(self, button: MouseButton) -> bool:
        return button in self._mouse_buttons_down

    def was_mouse_button_pressed(self, button: MouseButton) -> bool:
        return button in self._mouse_buttons_pressed

    def was_mouse_button_released(self, button: MouseButton) -> bool:
        return button in self._mouse_buttons_released
