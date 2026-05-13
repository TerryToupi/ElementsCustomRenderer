from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sdl3 as sdl

from Enums import TransferBufferUsage, to_sdl


@dataclass(slots=True)
class TransferBufferDescriptor:
    size: int
    usage: TransferBufferUsage | int = TransferBufferUsage.UPLOAD
    props: int = 0

    def to_sdl(self) -> sdl.SDL_GPUTransferBufferCreateInfo:
        info = sdl.SDL_GPUTransferBufferCreateInfo()
        info.usage = to_sdl(self.usage)
        info.size = self.size
        info.props = self.props
        return info


@dataclass(slots=True)
class TransferBuffer:
    handle: Any
    descriptor: TransferBufferDescriptor
