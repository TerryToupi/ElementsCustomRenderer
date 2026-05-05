from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sdl3 as sdl


@dataclass(slots=True)
class TextureDescriptor:
    width: int
    height: int
    format: int
    usage: int = sdl.SDL_GPU_TEXTUREUSAGE_SAMPLER
    type: int = sdl.SDL_GPU_TEXTURETYPE_2D
    layer_count_or_depth: int = 1
    num_levels: int = 1
    sample_count: int = sdl.SDL_GPU_SAMPLECOUNT_1
    props: int = 0

    def to_sdl(self) -> sdl.SDL_GPUTextureCreateInfo:
        info = sdl.SDL_GPUTextureCreateInfo()
        info.type = self.type
        info.format = self.format
        info.usage = self.usage
        info.width = self.width
        info.height = self.height
        info.layer_count_or_depth = self.layer_count_or_depth
        info.num_levels = self.num_levels
        info.sample_count = self.sample_count
        info.props = self.props
        return info


@dataclass(slots=True)
class Texture:
    handle: Any
    descriptor: TextureDescriptor
