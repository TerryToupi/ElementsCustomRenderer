from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sdl3 as sdl


@dataclass(slots=True)
class SamplerDescriptor:
    min_filter: int = sdl.SDL_GPU_FILTER_LINEAR
    mag_filter: int = sdl.SDL_GPU_FILTER_LINEAR
    mipmap_mode: int = sdl.SDL_GPU_SAMPLERMIPMAPMODE_LINEAR
    address_mode_u: int = sdl.SDL_GPU_SAMPLERADDRESSMODE_REPEAT
    address_mode_v: int = sdl.SDL_GPU_SAMPLERADDRESSMODE_REPEAT
    address_mode_w: int = sdl.SDL_GPU_SAMPLERADDRESSMODE_REPEAT
    mip_lod_bias: float = 0.0
    max_anisotropy: float = 1.0
    compare_op: int = sdl.SDL_GPU_COMPAREOP_INVALID
    min_lod: float = 0.0
    max_lod: float = 1000.0
    enable_anisotropy: bool = False
    enable_compare: bool = False
    props: int = 0

    def to_sdl(self) -> sdl.SDL_GPUSamplerCreateInfo:
        info = sdl.SDL_GPUSamplerCreateInfo()
        info.min_filter = self.min_filter
        info.mag_filter = self.mag_filter
        info.mipmap_mode = self.mipmap_mode
        info.address_mode_u = self.address_mode_u
        info.address_mode_v = self.address_mode_v
        info.address_mode_w = self.address_mode_w
        info.mip_lod_bias = self.mip_lod_bias
        info.max_anisotropy = self.max_anisotropy
        info.compare_op = self.compare_op
        info.min_lod = self.min_lod
        info.max_lod = self.max_lod
        info.enable_anisotropy = self.enable_anisotropy
        info.enable_compare = self.enable_compare
        info.props = self.props
        return info


@dataclass(slots=True)
class Sampler:
    handle: Any
    descriptor: SamplerDescriptor
