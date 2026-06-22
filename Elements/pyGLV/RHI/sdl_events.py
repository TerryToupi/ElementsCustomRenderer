from __future__ import annotations

from typing import Any

from ._sdl import sdl
from .events import (
    Event,
    KeyDownEvent,
    KeyUpEvent,
    MouseButtonDownEvent,
    MouseButtonUpEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    QuitEvent,
    WindowCloseEvent,
    WindowResizeEvent,
)
from .input import InputState, Key, MouseButton


def convert_sdl_event(event: Any) -> Event | None:
    event_type = getattr(event, "type", None)

    if event_type == getattr(sdl, "SDL_EVENT_QUIT", None):
        return QuitEvent()

    if event_type == getattr(sdl, "SDL_EVENT_WINDOW_CLOSE_REQUESTED", None):
        return WindowCloseEvent()

    if event_type in _WINDOW_RESIZE_EVENTS:
        return WindowResizeEvent(
            width=int(getattr(event.window, "data1", 0)),
            height=int(getattr(event.window, "data2", 0)),
        )

    if event_type == getattr(sdl, "SDL_EVENT_KEY_DOWN", None):
        return KeyDownEvent(
            key=key_from_sdl(getattr(event.key, "key", None)),
            repeat=bool(getattr(event.key, "repeat", False)),
        )

    if event_type == getattr(sdl, "SDL_EVENT_KEY_UP", None):
        return KeyUpEvent(key=key_from_sdl(getattr(event.key, "key", None)))

    if event_type == getattr(sdl, "SDL_EVENT_MOUSE_MOTION", None):
        return MouseMoveEvent(
            x=float(getattr(event.motion, "x", 0.0)),
            y=float(getattr(event.motion, "y", 0.0)),
            dx=float(getattr(event.motion, "xrel", 0.0)),
            dy=float(getattr(event.motion, "yrel", 0.0)),
        )

    if event_type == getattr(sdl, "SDL_EVENT_MOUSE_BUTTON_DOWN", None):
        return MouseButtonDownEvent(
            button=mouse_button_from_sdl(getattr(event.button, "button", None)),
            x=float(getattr(event.button, "x", 0.0)),
            y=float(getattr(event.button, "y", 0.0)),
            clicks=int(getattr(event.button, "clicks", 1)),
        )

    if event_type == getattr(sdl, "SDL_EVENT_MOUSE_BUTTON_UP", None):
        return MouseButtonUpEvent(
            button=mouse_button_from_sdl(getattr(event.button, "button", None)),
            x=float(getattr(event.button, "x", 0.0)),
            y=float(getattr(event.button, "y", 0.0)),
            clicks=int(getattr(event.button, "clicks", 1)),
        )

    if event_type == getattr(sdl, "SDL_EVENT_MOUSE_WHEEL", None):
        wheel_x = float(getattr(event.wheel, "x", 0.0))
        wheel_y = float(getattr(event.wheel, "y", 0.0))
        if getattr(event.wheel, "direction", None) == getattr(
            sdl,
            "SDL_MOUSEWHEEL_FLIPPED",
            object(),
        ):
            wheel_x = -wheel_x
            wheel_y = -wheel_y
        return MouseWheelEvent(
            x=wheel_x,
            y=wheel_y,
            mouse_x=float(getattr(event.wheel, "mouse_x", 0.0)),
            mouse_y=float(getattr(event.wheel, "mouse_y", 0.0)),
        )

    return None


def convert_sdl_events(events: list[Any]) -> list[Event]:
    converted: list[Event] = []
    for event in events:
        engine_event = convert_sdl_event(event)
        if engine_event is not None:
            converted.append(engine_event)
    return converted


def update_input_state(input_state: InputState, events: list[Event]) -> None:
    for event in events:
        if isinstance(event, KeyDownEvent):
            input_state.press_key(event.key, event.repeat)
        elif isinstance(event, KeyUpEvent):
            input_state.release_key(event.key)
        elif isinstance(event, MouseMoveEvent):
            input_state.move_mouse(event.x, event.y, event.dx, event.dy)
        elif isinstance(event, MouseButtonDownEvent):
            input_state.press_mouse_button(event.button, event.x, event.y)
        elif isinstance(event, MouseButtonUpEvent):
            input_state.release_mouse_button(event.button, event.x, event.y)
        elif isinstance(event, MouseWheelEvent):
            input_state.scroll_mouse(event.x, event.y)


def key_from_sdl(key_code: Any) -> Key:
    return _KEY_MAP.get(_int_value(key_code), Key.UNKNOWN)


def mouse_button_from_sdl(button_code: Any) -> MouseButton:
    return _MOUSE_BUTTON_MAP.get(_int_value(button_code), MouseButton.UNKNOWN)


def _int_value(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _sdl_constant(name: str) -> int | None:
    return _int_value(getattr(sdl, name, None))


def _add_key(mapping: dict[int, Key], name: str, key: Key) -> None:
    value = _sdl_constant(name)
    if value is not None:
        mapping[value] = key


def _build_key_map() -> dict[int, Key]:
    mapping: dict[int, Key] = {}

    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        _add_key(mapping, f"SDLK_{letter}", Key[letter])

    for digit in range(10):
        _add_key(mapping, f"SDLK_{digit}", Key[f"NUM_{digit}"])

    for index in range(1, 13):
        _add_key(mapping, f"SDLK_F{index}", Key[f"F{index}"])

    _add_key(mapping, "SDLK_ESCAPE", Key.ESCAPE)
    _add_key(mapping, "SDLK_RETURN", Key.ENTER)
    _add_key(mapping, "SDLK_RETURN2", Key.ENTER)
    _add_key(mapping, "SDLK_KP_ENTER", Key.ENTER)
    _add_key(mapping, "SDLK_SPACE", Key.SPACE)
    _add_key(mapping, "SDLK_BACKSPACE", Key.BACKSPACE)
    _add_key(mapping, "SDLK_TAB", Key.TAB)
    _add_key(mapping, "SDLK_LSHIFT", Key.SHIFT)
    _add_key(mapping, "SDLK_RSHIFT", Key.SHIFT)
    _add_key(mapping, "SDLK_LCTRL", Key.CONTROL)
    _add_key(mapping, "SDLK_RCTRL", Key.CONTROL)
    _add_key(mapping, "SDLK_LALT", Key.ALT)
    _add_key(mapping, "SDLK_RALT", Key.ALT)
    _add_key(mapping, "SDLK_LEFT", Key.LEFT)
    _add_key(mapping, "SDLK_RIGHT", Key.RIGHT)
    _add_key(mapping, "SDLK_UP", Key.UP)
    _add_key(mapping, "SDLK_DOWN", Key.DOWN)

    return mapping


def _build_mouse_button_map() -> dict[int, MouseButton]:
    mapping: dict[int, MouseButton] = {}
    button_names = {
        "SDL_BUTTON_LEFT": MouseButton.LEFT,
        "SDL_BUTTON_RIGHT": MouseButton.RIGHT,
        "SDL_BUTTON_MIDDLE": MouseButton.MIDDLE,
        "SDL_BUTTON_X1": MouseButton.X1,
        "SDL_BUTTON_X2": MouseButton.X2,
    }
    for name, button in button_names.items():
        value = _sdl_constant(name)
        if value is not None:
            mapping[value] = button
    return mapping


_WINDOW_RESIZE_EVENTS = {
    getattr(sdl, "SDL_EVENT_WINDOW_RESIZED", object()),
    getattr(sdl, "SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED", object()),
}
_KEY_MAP = _build_key_map()
_MOUSE_BUTTON_MAP = _build_mouse_button_map()
