from __future__ import annotations

import ctypes
from dataclasses import dataclass, field
from typing import Any, Sequence

from .._sdl import sdl

from ..Enums import (
    CompareOp,
    CullMode,
    FillMode,
    FrontFace,
    PrimitiveType,
    SampleCount,
    TextureFormat,
    VertexElementFormat,
    VertexInputRate,
    to_sdl,
)


@dataclass(frozen=True)
class VertexBufferDescription:
    slot: int
    pitch: int
    input_rate: VertexInputRate | int = VertexInputRate.VERTEX
    instance_step_rate: int = 0


@dataclass(frozen=True)
class VertexAttribute:
    location: int
    buffer_slot: int
    format: VertexElementFormat | int
    offset: int


@dataclass
class GraphicsPipelineDescriptor:
    vertex_shader: Any
    fragment_shader: Any | None = None
    color_target_formats: Sequence[TextureFormat | int] = field(default_factory=tuple)
    vertex_buffer_descriptions: Sequence[VertexBufferDescription] = field(
        default_factory=tuple
    )
    vertex_attributes: Sequence[VertexAttribute] = field(default_factory=tuple)
    primitive_type: PrimitiveType | int = PrimitiveType.TRIANGLELIST
    fill_mode: FillMode | int = FillMode.FILL
    cull_mode: CullMode | int = CullMode.NONE
    front_face: FrontFace | int = FrontFace.COUNTER_CLOCKWISE
    sample_count: SampleCount | int = SampleCount.SAMPLE_1
    sample_mask: int = 0
    depth_stencil_format: TextureFormat | int = TextureFormat.INVALID
    has_depth_stencil_target: bool = False
    enable_depth_test: bool = False
    enable_depth_write: bool = False
    depth_compare_op: CompareOp | int = CompareOp.INVALID
    props: int = 0

    def to_sdl(
        self,
        vertex_shader_handle: Any,
        fragment_shader_handle: Any | None,
    ) -> tuple[sdl.SDL_GPUGraphicsPipelineCreateInfo, list[Any]]:
        info = sdl.SDL_GPUGraphicsPipelineCreateInfo()
        info.vertex_shader = vertex_shader_handle
        info.fragment_shader = fragment_shader_handle
        keep_alive: list[Any] = []

        if self.vertex_buffer_descriptions:
            buffer_descriptions = (
                sdl.SDL_GPUVertexBufferDescription
                * len(self.vertex_buffer_descriptions)
            )()
            for index, description in enumerate(self.vertex_buffer_descriptions):
                buffer_descriptions[index].slot = description.slot
                buffer_descriptions[index].pitch = description.pitch
                buffer_descriptions[index].input_rate = to_sdl(description.input_rate)
                buffer_descriptions[index].instance_step_rate = (
                    description.instance_step_rate
                )
            info.vertex_input_state.vertex_buffer_descriptions = ctypes.cast(
                buffer_descriptions,
                ctypes.POINTER(sdl.SDL_GPUVertexBufferDescription),
            )
            info.vertex_input_state.num_vertex_buffers = len(
                self.vertex_buffer_descriptions
            )
            keep_alive.append(buffer_descriptions)

        if self.vertex_attributes:
            attributes = (
                sdl.SDL_GPUVertexAttribute * len(self.vertex_attributes)
            )()
            for index, attribute in enumerate(self.vertex_attributes):
                attributes[index].location = attribute.location
                attributes[index].buffer_slot = attribute.buffer_slot
                attributes[index].format = to_sdl(attribute.format)
                attributes[index].offset = attribute.offset
            info.vertex_input_state.vertex_attributes = ctypes.cast(
                attributes,
                ctypes.POINTER(sdl.SDL_GPUVertexAttribute),
            )
            info.vertex_input_state.num_vertex_attributes = len(self.vertex_attributes)
            keep_alive.append(attributes)

        info.primitive_type = to_sdl(self.primitive_type)
        info.rasterizer_state.fill_mode = to_sdl(self.fill_mode)
        info.rasterizer_state.cull_mode = to_sdl(self.cull_mode)
        info.rasterizer_state.front_face = to_sdl(self.front_face)
        info.multisample_state.sample_count = to_sdl(self.sample_count)
        info.multisample_state.sample_mask = self.sample_mask
        info.depth_stencil_state.compare_op = to_sdl(self.depth_compare_op)
        info.depth_stencil_state.enable_depth_test = self.enable_depth_test
        info.depth_stencil_state.enable_depth_write = self.enable_depth_write
        info.target_info.depth_stencil_format = to_sdl(self.depth_stencil_format)
        info.target_info.has_depth_stencil_target = self.has_depth_stencil_target
        info.props = self.props

        if self.color_target_formats:
            color_targets = (
                sdl.SDL_GPUColorTargetDescription * len(self.color_target_formats)
            )()
            for index, format in enumerate(self.color_target_formats):
                color_targets[index].format = to_sdl(format)
            info.target_info.num_color_targets = len(self.color_target_formats)
            info.target_info.color_target_descriptions = ctypes.cast(
                color_targets,
                ctypes.POINTER(sdl.SDL_GPUColorTargetDescription),
            )
            keep_alive.append(color_targets)

        return info, keep_alive


@dataclass
class GraphicsPipeline:
    handle: Any
    descriptor: GraphicsPipelineDescriptor
