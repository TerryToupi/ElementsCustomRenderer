from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sdl3 as sdl

from Enums import BufferUsage, to_sdl


@dataclass(slots=True)
class BufferDescriptor:
    size: int
    usage: BufferUsage | int = BufferUsage.VERTEX
    props: int = 0

    def to_sdl(self) -> sdl.SDL_GPUBufferCreateInfo:
        info = sdl.SDL_GPUBufferCreateInfo()
        info.usage = to_sdl(self.usage)
        info.size = self.size
        info.props = self.props
        return info


@dataclass(slots=True)
class Buffer:
    handle: Any
    descriptor: BufferDescriptor
