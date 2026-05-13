from __future__ import annotations

from typing import Any

import sdl3 as sdl

from Errors import RendererError


class SdlError(RendererError):
    pass


def error_message() -> str:
    message = sdl.SDL_GetError()
    if not message:
        return "unknown SDL error"
    return message.decode("utf-8", errors="replace")


def check(value: Any, what: str) -> Any:
    if not value:
        raise SdlError(f"{what}: {error_message()}")
    return value


def to_bytes(value: str | bytes | None) -> bytes | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    return value.encode("utf-8")
