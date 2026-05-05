from __future__ import annotations

import base64
import ctypes
from dataclasses import dataclass
from typing import Any

import sdl3 as sdl

from Utils.Sdl import to_bytes


@dataclass(slots=True)
class ShaderDescriptor:
    code: bytes
    stage: int
    format: int = sdl.SDL_GPU_SHADERFORMAT_SPIRV
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
        stage: int,
        format: int = sdl.SDL_GPU_SHADERFORMAT_SPIRV,
        entrypoint: str | bytes = "main",
    ) -> "ShaderDescriptor":
        return cls(
            code=base64.b64decode(data_b64),
            stage=stage,
            format=format,
            entrypoint=entrypoint,
        )

    def to_sdl(self) -> tuple[sdl.SDL_GPUShaderCreateInfo, list[Any]]:
        code = (ctypes.c_uint8 * len(self.code)).from_buffer_copy(self.code)
        entrypoint = to_bytes(self.entrypoint)

        info = sdl.SDL_GPUShaderCreateInfo()
        info.code_size = len(self.code)
        info.code = ctypes.cast(code, ctypes.POINTER(ctypes.c_uint8))
        info.entrypoint = entrypoint
        info.format = self.format
        info.stage = self.stage
        info.num_samplers = self.num_samplers
        info.num_storage_textures = self.num_storage_textures
        info.num_storage_buffers = self.num_storage_buffers
        info.num_uniform_buffers = self.num_uniform_buffers
        info.props = self.props
        return info, [code, entrypoint]


@dataclass(slots=True)
class Shader:
    handle: Any
    descriptor: ShaderDescriptor
