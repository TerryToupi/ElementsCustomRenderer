from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sdl3 as sdl


@dataclass(slots=True)
class TransferBufferDescriptor:
    size: int
    usage: int = sdl.SDL_GPU_TRANSFERBUFFERUSAGE_UPLOAD
    props: int = 0

    def to_sdl(self) -> sdl.SDL_GPUTransferBufferCreateInfo:
        info = sdl.SDL_GPUTransferBufferCreateInfo()
        info.usage = self.usage
        info.size = self.size
        info.props = self.props
        return info


@dataclass(slots=True)
class TransferBuffer:
    handle: Any
    descriptor: TransferBufferDescriptor
