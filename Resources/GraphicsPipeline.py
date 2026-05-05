from __future__ import annotations

import ctypes
from dataclasses import dataclass, field
from typing import Any, Sequence

import sdl3 as sdl


@dataclass(slots=True)
class GraphicsPipelineDescriptor:
    vertex_shader: Any
    fragment_shader: Any | None = None
    color_target_formats: Sequence[int] = field(default_factory=tuple)
    primitive_type: int = sdl.SDL_GPU_PRIMITIVETYPE_TRIANGLELIST
    fill_mode: int = sdl.SDL_GPU_FILLMODE_FILL
    cull_mode: int = sdl.SDL_GPU_CULLMODE_NONE
    front_face: int = sdl.SDL_GPU_FRONTFACE_COUNTER_CLOCKWISE
    sample_count: int = sdl.SDL_GPU_SAMPLECOUNT_1
    sample_mask: int = 0
    depth_stencil_format: int = sdl.SDL_GPU_TEXTUREFORMAT_INVALID
    has_depth_stencil_target: bool = False
    enable_depth_test: bool = False
    enable_depth_write: bool = False
    depth_compare_op: int = sdl.SDL_GPU_COMPAREOP_INVALID
    props: int = 0

    def to_sdl(
        self,
        vertex_shader_handle: Any,
        fragment_shader_handle: Any | None,
    ) -> tuple[sdl.SDL_GPUGraphicsPipelineCreateInfo, list[Any]]:
        info = sdl.SDL_GPUGraphicsPipelineCreateInfo()
        info.vertex_shader = vertex_shader_handle
        info.fragment_shader = fragment_shader_handle
        info.primitive_type = self.primitive_type
        info.rasterizer_state.fill_mode = self.fill_mode
        info.rasterizer_state.cull_mode = self.cull_mode
        info.rasterizer_state.front_face = self.front_face
        info.multisample_state.sample_count = self.sample_count
        info.multisample_state.sample_mask = self.sample_mask
        info.depth_stencil_state.compare_op = self.depth_compare_op
        info.depth_stencil_state.enable_depth_test = self.enable_depth_test
        info.depth_stencil_state.enable_depth_write = self.enable_depth_write
        info.target_info.depth_stencil_format = self.depth_stencil_format
        info.target_info.has_depth_stencil_target = self.has_depth_stencil_target
        info.props = self.props

        keep_alive: list[Any] = []
        if self.color_target_formats:
            color_targets = (
                sdl.SDL_GPUColorTargetDescription * len(self.color_target_formats)
            )()
            for index, format in enumerate(self.color_target_formats):
                color_targets[index].format = format
            info.target_info.num_color_targets = len(self.color_target_formats)
            info.target_info.color_target_descriptions = ctypes.cast(
                color_targets,
                ctypes.POINTER(sdl.SDL_GPUColorTargetDescription),
            )
            keep_alive.append(color_targets)

        return info, keep_alive


@dataclass(slots=True)
class GraphicsPipeline:
    handle: Any
    descriptor: GraphicsPipelineDescriptor
