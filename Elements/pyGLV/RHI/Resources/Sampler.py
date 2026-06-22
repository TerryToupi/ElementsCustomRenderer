from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .._sdl import sdl

from ..Enums import (
    CompareOp,
    Filter,
    SamplerAddressMode,
    SamplerMipmapMode,
    to_sdl,
)


@dataclass
class SamplerDescriptor:
    min_filter: Filter | int = Filter.LINEAR
    mag_filter: Filter | int = Filter.LINEAR
    mipmap_mode: SamplerMipmapMode | int = SamplerMipmapMode.LINEAR
    address_mode_u: SamplerAddressMode | int = SamplerAddressMode.REPEAT
    address_mode_v: SamplerAddressMode | int = SamplerAddressMode.REPEAT
    address_mode_w: SamplerAddressMode | int = SamplerAddressMode.REPEAT
    mip_lod_bias: float = 0.0
    max_anisotropy: float = 1.0
    compare_op: CompareOp | int = CompareOp.INVALID
    min_lod: float = 0.0
    max_lod: float = 1000.0
    enable_anisotropy: bool = False
    enable_compare: bool = False
    props: int = 0

    def to_sdl(self) -> sdl.SDL_GPUSamplerCreateInfo:
        info = sdl.SDL_GPUSamplerCreateInfo()
        info.min_filter = to_sdl(self.min_filter)
        info.mag_filter = to_sdl(self.mag_filter)
        info.mipmap_mode = to_sdl(self.mipmap_mode)
        info.address_mode_u = to_sdl(self.address_mode_u)
        info.address_mode_v = to_sdl(self.address_mode_v)
        info.address_mode_w = to_sdl(self.address_mode_w)
        info.mip_lod_bias = self.mip_lod_bias
        info.max_anisotropy = self.max_anisotropy
        info.compare_op = to_sdl(self.compare_op)
        info.min_lod = self.min_lod
        info.max_lod = self.max_lod
        info.enable_anisotropy = self.enable_anisotropy
        info.enable_compare = self.enable_compare
        info.props = self.props
        return info


@dataclass
class Sampler:
    handle: Any
    descriptor: SamplerDescriptor
