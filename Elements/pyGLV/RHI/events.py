from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .input import Key, MouseButton


class EventType(Enum):
    QUIT = "quit"
    WINDOW_RESIZE = "window_resize"
    WINDOW_CLOSE = "window_close"
    KEY_DOWN = "key_down"
    KEY_UP = "key_up"
    MOUSE_MOVE = "mouse_move"
    MOUSE_BUTTON_DOWN = "mouse_button_down"
    MOUSE_BUTTON_UP = "mouse_button_up"
    MOUSE_WHEEL = "mouse_wheel"


class Event:
    type: EventType


@dataclass(frozen=True)
class QuitEvent(Event):
    type: EventType = field(default=EventType.QUIT, init=False)


@dataclass(frozen=True)
class WindowResizeEvent(Event):
    width: int = 0
    height: int = 0
    type: EventType = field(default=EventType.WINDOW_RESIZE, init=False)


@dataclass(frozen=True)
class WindowCloseEvent(Event):
    type: EventType = field(default=EventType.WINDOW_CLOSE, init=False)


@dataclass(frozen=True)
class KeyDownEvent(Event):
    key: Key = Key.UNKNOWN
    repeat: bool = False
    type: EventType = field(default=EventType.KEY_DOWN, init=False)


@dataclass(frozen=True)
class KeyUpEvent(Event):
    key: Key = Key.UNKNOWN
    type: EventType = field(default=EventType.KEY_UP, init=False)


@dataclass(frozen=True)
class MouseMoveEvent(Event):
    x: float = 0.0
    y: float = 0.0
    dx: float = 0.0
    dy: float = 0.0
    type: EventType = field(default=EventType.MOUSE_MOVE, init=False)


@dataclass(frozen=True)
class MouseButtonDownEvent(Event):
    button: MouseButton = MouseButton.UNKNOWN
    x: float = 0.0
    y: float = 0.0
    clicks: int = 1
    type: EventType = field(default=EventType.MOUSE_BUTTON_DOWN, init=False)


@dataclass(frozen=True)
class MouseButtonUpEvent(Event):
    button: MouseButton = MouseButton.UNKNOWN
    x: float = 0.0
    y: float = 0.0
    clicks: int = 1
    type: EventType = field(default=EventType.MOUSE_BUTTON_UP, init=False)


@dataclass(frozen=True)
class MouseWheelEvent(Event):
    x: float = 0.0
    y: float = 0.0
    mouse_x: float = 0.0
    mouse_y: float = 0.0
    type: EventType = field(default=EventType.MOUSE_WHEEL, init=False)
