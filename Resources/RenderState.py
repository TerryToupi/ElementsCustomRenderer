from __future__ import annotations

import ctypes
from dataclasses import dataclass, field
from typing import Any

import sdl3 as sdl


@dataclass(slots=True)
class TextureSamplerBindingDescriptor:
    texture: Any
    sampler: Any


@dataclass(slots=True)
class RenderStateDescriptor:
    fragment_shader: Any
    sampler_bindings: tuple[TextureSamplerBindingDescriptor, ...] = field(default_factory=tuple)
    storage_textures: tuple[Any, ...] = field(default_factory=tuple)
    storage_buffers: tuple[Any, ...] = field(default_factory=tuple)
    props: int = 0

    def to_sdl(
        self,
        fragment_shader_handle: Any,
        sampler_bindings: list[tuple[Any, Any]],
        storage_texture_handles: list[Any],
        storage_buffer_handles: list[Any],
    ) -> tuple[sdl.SDL_GPURenderStateCreateInfo, list[Any]]:
        info = sdl.SDL_GPURenderStateCreateInfo()
        info.fragment_shader = fragment_shader_handle
        info.props = self.props

        keep_alive: list[Any] = []

        if sampler_bindings:
            binding_array = (
                sdl.SDL_GPUTextureSamplerBinding * len(sampler_bindings)
            )()
            for index, (texture, sampler) in enumerate(sampler_bindings):
                binding_array[index].texture = texture
                binding_array[index].sampler = sampler
            info.num_sampler_bindings = len(sampler_bindings)
            info.sampler_bindings = ctypes.cast(
                binding_array,
                ctypes.POINTER(sdl.SDL_GPUTextureSamplerBinding),
            )
            keep_alive.append(binding_array)

        if storage_texture_handles:
            texture_array = (
                type(storage_texture_handles[0]) * len(storage_texture_handles)
            )(*storage_texture_handles)
            info.num_storage_textures = len(storage_texture_handles)
            info.storage_textures = texture_array
            keep_alive.append(texture_array)

        if storage_buffer_handles:
            buffer_array = (
                type(storage_buffer_handles[0]) * len(storage_buffer_handles)
            )(*storage_buffer_handles)
            info.num_storage_buffers = len(storage_buffer_handles)
            info.storage_buffers = buffer_array
            keep_alive.append(buffer_array)

        return info, keep_alive


@dataclass(slots=True)
class RenderState:
    handle: Any
    descriptor: RenderStateDescriptor
