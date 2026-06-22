from __future__ import annotations

import base64
import ctypes
from dataclasses import dataclass
from typing import Any

from .._sdl import sdl

from ..Enums import ShaderFormat, ShaderStage, to_sdl
from ..Utils.Sdl import to_bytes


@dataclass
class ShaderDescriptor:
    code: bytes
    stage: ShaderStage | int
    format: ShaderFormat | int = ShaderFormat.SPIRV
    entrypoint: str | bytes = "main"
    num_samplers: int = 0
    num_storage_textures: int = 0
    num_storage_buffers: int = 0
    num_uniform_buffers: int = 0
    props: int = 0

    @classmethod
    def from_base64(
        cls,
        data_b64: str,
        stage: ShaderStage | int,
        format: ShaderFormat | int = ShaderFormat.SPIRV,
        entrypoint: str | bytes = "main",
        num_samplers: int = 0,
        num_storage_textures: int = 0,
        num_storage_buffers: int = 0,
        num_uniform_buffers: int = 0,
    ) -> "ShaderDescriptor":
        return cls(
            code=base64.b64decode(data_b64),
            stage=stage,
            format=format,
            entrypoint=entrypoint,
            num_samplers=num_samplers,
            num_storage_textures=num_storage_textures,
            num_storage_buffers=num_storage_buffers,
            num_uniform_buffers=num_uniform_buffers,
        )

    def to_sdl(self) -> tuple[sdl.SDL_GPUShaderCreateInfo, list[Any]]:
        code = (ctypes.c_uint8 * len(self.code)).from_buffer_copy(self.code)
        entrypoint = to_bytes(self.entrypoint)

        info = sdl.SDL_GPUShaderCreateInfo()
        info.code_size = len(self.code)
        info.code = ctypes.cast(code, ctypes.POINTER(ctypes.c_uint8))
        info.entrypoint = entrypoint
        info.format = to_sdl(self.format)
        info.stage = to_sdl(self.stage)
        info.num_samplers = self.num_samplers
        info.num_storage_textures = self.num_storage_textures
        info.num_storage_buffers = self.num_storage_buffers
        info.num_uniform_buffers = self.num_uniform_buffers
        info.props = self.props
        return info, [code, entrypoint]


@dataclass
class Shader:
    handle: Any
    descriptor: ShaderDescriptor
