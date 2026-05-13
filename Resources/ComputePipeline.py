from __future__ import annotations

import ctypes
from dataclasses import dataclass
from typing import Any

import sdl3 as sdl

from Enums import ShaderFormat, to_sdl
from Utils.Sdl import to_bytes


@dataclass(slots=True)
class ComputePipelineDescriptor:
    code: bytes
    format: ShaderFormat | int = ShaderFormat.SPIRV
    entrypoint: str | bytes = "main"
    num_samplers: int = 0
    num_readonly_storage_textures: int = 0
    num_readonly_storage_buffers: int = 0
    num_readwrite_storage_textures: int = 0
    num_readwrite_storage_buffers: int = 0
    num_uniform_buffers: int = 0
    threadcount_x: int = 1
    threadcount_y: int = 1
    threadcount_z: int = 1
    props: int = 0

    def to_sdl(self) -> tuple[sdl.SDL_GPUComputePipelineCreateInfo, list[Any]]:
        code = (ctypes.c_uint8 * len(self.code)).from_buffer_copy(self.code)
        entrypoint = to_bytes(self.entrypoint)

        info = sdl.SDL_GPUComputePipelineCreateInfo()
        info.code_size = len(self.code)
        info.code = ctypes.cast(code, ctypes.POINTER(ctypes.c_uint8))
        info.entrypoint = entrypoint
        info.format = to_sdl(self.format)
        info.num_samplers = self.num_samplers
        info.num_readonly_storage_textures = self.num_readonly_storage_textures
        info.num_readonly_storage_buffers = self.num_readonly_storage_buffers
        info.num_readwrite_storage_textures = self.num_readwrite_storage_textures
        info.num_readwrite_storage_buffers = self.num_readwrite_storage_buffers
        info.num_uniform_buffers = self.num_uniform_buffers
        info.threadcount_x = self.threadcount_x
        info.threadcount_y = self.threadcount_y
        info.threadcount_z = self.threadcount_z
        info.props = self.props
        return info, [code, entrypoint]


@dataclass(slots=True)
class ComputePipeline:
    handle: Any
    descriptor: ComputePipelineDescriptor
