from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sdl3 as sdl

from Enums import SampleCount, TextureFormat, TextureType, TextureUsage, to_sdl


@dataclass(slots=True)
class TextureDescriptor:
    width: int
    height: int
    format: TextureFormat | int
    usage: TextureUsage | int = TextureUsage.SAMPLER
    type: TextureType | int = TextureType.TEXTURE_2D
    layer_count_or_depth: int = 1
    num_levels: int = 1
    sample_count: SampleCount | int = SampleCount.SAMPLE_1
    props: int = 0

    def to_sdl(self) -> sdl.SDL_GPUTextureCreateInfo:
        info = sdl.SDL_GPUTextureCreateInfo()
        info.type = to_sdl(self.type)
        info.format = to_sdl(self.format)
        info.usage = to_sdl(self.usage)
        info.width = self.width
        info.height = self.height
        info.layer_count_or_depth = self.layer_count_or_depth
        info.num_levels = self.num_levels
        info.sample_count = to_sdl(self.sample_count)
        info.props = self.props
        return info


@dataclass(slots=True)
class Texture:
    handle: Any
    descriptor: TextureDescriptor
