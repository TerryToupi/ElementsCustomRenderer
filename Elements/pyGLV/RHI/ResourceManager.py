from __future__ import annotations

import ctypes
from typing import Any

from ._sdl import sdl

from .Enums import BufferUsage, TransferBufferUsage
from .Resources.BindGroup import BindGroup, BindGroupDescriptor
from .Resources.BindGroupLayout import BindGroupLayout, BindGroupLayoutDescriptor
from .Resources.Buffer import Buffer, BufferDescriptor
from .Resources.ComputePipeline import ComputePipeline, ComputePipelineDescriptor
from .Resources.GraphicsPipeline import GraphicsPipeline, GraphicsPipelineDescriptor
from .Resources.RenderState import RenderState, RenderStateDescriptor
from .Resources.Sampler import Sampler, SamplerDescriptor
from .Resources.Shader import Shader, ShaderDescriptor
from .Resources.Texture import Texture, TextureDescriptor
from .Resources.TransferBuffer import TransferBuffer, TransferBufferDescriptor
from .Utils.Pool import Pool, PoolHandle
from .Utils.Sdl import check


TextureHandle = PoolHandle[Texture]
BufferHandle = PoolHandle[Buffer]
SamplerHandle = PoolHandle[Sampler]
ShaderHandle = PoolHandle[Shader]
TransferBufferHandle = PoolHandle[TransferBuffer]
GraphicsPipelineHandle = PoolHandle[GraphicsPipeline]
ComputePipelineHandle = PoolHandle[ComputePipeline]
BindGroupLayoutHandle = PoolHandle[BindGroupLayout]
BindGroupHandle = PoolHandle[BindGroup]
RenderStateHandle = PoolHandle[RenderState]


class ResourceManager:
    def __init__(self, device: Any):
        self.device = getattr(device, "raw", getattr(device, "handle", device))

        self.textures: Pool[Texture] = Pool()
        self.buffers: Pool[Buffer] = Pool()
        self.samplers: Pool[Sampler] = Pool()
        self.shaders: Pool[Shader] = Pool()
        self.transfer_buffers: Pool[TransferBuffer] = Pool()
        self.graphics_pipelines: Pool[GraphicsPipeline] = Pool()
        self.compute_pipelines: Pool[ComputePipeline] = Pool()
        self.bind_group_layouts: Pool[BindGroupLayout] = Pool()
        self.bind_groups: Pool[BindGroup] = Pool()
        self.render_states: Pool[RenderState] = Pool()

    def create_texture(self, descriptor: TextureDescriptor) -> TextureHandle:
        info = descriptor.to_sdl()
        handle = check(
            sdl.SDL_CreateGPUTexture(self.device, ctypes.byref(info)),
            "SDL_CreateGPUTexture",
        )
        return self.textures.add(Texture(handle, descriptor))

    def get_texture(self, handle: TextureHandle) -> Texture:
        return self.textures.get(handle)

    def destroy_texture(self, handle: TextureHandle) -> None:
        texture = self.textures.remove(handle)
        sdl.SDL_ReleaseGPUTexture(self.device, texture.handle)

    def create_buffer(self, descriptor: BufferDescriptor) -> BufferHandle:
        info = descriptor.to_sdl()
        handle = check(
            sdl.SDL_CreateGPUBuffer(self.device, ctypes.byref(info)),
            "SDL_CreateGPUBuffer",
        )
        return self.buffers.add(Buffer(handle, descriptor))

    def create_buffer_with_data(
        self,
        data: Any,
        usage: BufferUsage | int = BufferUsage.VERTEX,
    ) -> BufferHandle:
        payload = self._payload_bytes(data)
        handle = self.create_buffer(BufferDescriptor(size=len(payload), usage=usage))
        self.upload_buffer(handle, payload)
        return handle

    def get_buffer(self, handle: BufferHandle) -> Buffer:
        return self.buffers.get(handle)

    def upload_buffer(
        self,
        handle: BufferHandle | Any,
        data: Any,
        offset: int = 0,
        cycle: bool = True,
    ) -> None:
        payload = self._payload_bytes(data)
        if not payload:
            return

        transfer_handle = self.create_transfer_buffer(
            TransferBufferDescriptor(
                size=len(payload),
                usage=TransferBufferUsage.UPLOAD,
            )
        )
        transfer = self.get_transfer_buffer(transfer_handle)
        command_buffer = None

        try:
            mapped = check(
                sdl.SDL_MapGPUTransferBuffer(self.device, transfer.handle, False),
                "SDL_MapGPUTransferBuffer",
            )
            ctypes.memmove(mapped, payload, len(payload))
            sdl.SDL_UnmapGPUTransferBuffer(self.device, transfer.handle)

            command_buffer = check(
                sdl.SDL_AcquireGPUCommandBuffer(self.device),
                "SDL_AcquireGPUCommandBuffer",
            )
            copy_pass = check(
                sdl.SDL_BeginGPUCopyPass(command_buffer),
                "SDL_BeginGPUCopyPass",
            )

            source = sdl.SDL_GPUTransferBufferLocation()
            source.transfer_buffer = transfer.handle
            source.offset = 0

            destination = sdl.SDL_GPUBufferRegion()
            destination.buffer = self._buffer_handle(handle)
            destination.offset = offset
            destination.size = len(payload)

            sdl.SDL_UploadToGPUBuffer(
                copy_pass,
                ctypes.byref(source),
                ctypes.byref(destination),
                cycle,
            )
            sdl.SDL_EndGPUCopyPass(copy_pass)
            check(
                sdl.SDL_SubmitGPUCommandBuffer(command_buffer),
                "SDL_SubmitGPUCommandBuffer",
            )
            command_buffer = None
        except Exception:
            if command_buffer is not None:
                sdl.SDL_CancelGPUCommandBuffer(command_buffer)
            raise
        finally:
            self.destroy_transfer_buffer(transfer_handle)

    def download_buffer(
        self,
        handle: BufferHandle | Any,
        size: int | None = None,
        offset: int = 0,
    ) -> bytes:
        # Readback is a two-step GPU operation:
        # 1. copy GPU buffer -> download transfer buffer,
        # 2. map the transfer buffer so Python can read the bytes.
        buffer = self.get_buffer(handle) if isinstance(handle, PoolHandle) else handle
        byte_count = int(
            size if size is not None else buffer.descriptor.size - offset
        )
        if byte_count <= 0:
            return b""

        transfer_handle = self.create_transfer_buffer(
            TransferBufferDescriptor(
                size=byte_count,
                usage=TransferBufferUsage.DOWNLOAD,
            )
        )
        transfer = self.get_transfer_buffer(transfer_handle)
        command_buffer = None
        fence = None

        try:
            command_buffer = check(
                sdl.SDL_AcquireGPUCommandBuffer(self.device),
                "SDL_AcquireGPUCommandBuffer",
            )
            copy_pass = check(
                sdl.SDL_BeginGPUCopyPass(command_buffer),
                "SDL_BeginGPUCopyPass",
            )

            source = sdl.SDL_GPUBufferRegion()
            source.buffer = self._buffer_handle(handle)
            source.offset = offset
            source.size = byte_count

            destination = sdl.SDL_GPUTransferBufferLocation()
            destination.transfer_buffer = transfer.handle
            destination.offset = 0

            sdl.SDL_DownloadFromGPUBuffer(
                copy_pass,
                ctypes.byref(source),
                ctypes.byref(destination),
            )
            sdl.SDL_EndGPUCopyPass(copy_pass)

            fence = check(
                sdl.SDL_SubmitGPUCommandBufferAndAcquireFence(command_buffer),
                "SDL_SubmitGPUCommandBufferAndAcquireFence",
            )
            command_buffer = None

            fences = (type(fence) * 1)(fence)
            check(
                sdl.SDL_WaitForGPUFences(self.device, True, fences, 1),
                "SDL_WaitForGPUFences",
            )

            mapped = check(
                sdl.SDL_MapGPUTransferBuffer(self.device, transfer.handle, False),
                "SDL_MapGPUTransferBuffer",
            )
            try:
                return ctypes.string_at(mapped, byte_count)
            finally:
                sdl.SDL_UnmapGPUTransferBuffer(self.device, transfer.handle)
        except Exception:
            if command_buffer is not None:
                sdl.SDL_CancelGPUCommandBuffer(command_buffer)
            raise
        finally:
            if fence is not None:
                sdl.SDL_ReleaseGPUFence(self.device, fence)
            self.destroy_transfer_buffer(transfer_handle)

    def destroy_buffer(self, handle: BufferHandle) -> None:
        buffer = self.buffers.remove(handle)
        sdl.SDL_ReleaseGPUBuffer(self.device, buffer.handle)

    def create_sampler(self, descriptor: SamplerDescriptor) -> SamplerHandle:
        info = descriptor.to_sdl()
        handle = check(
            sdl.SDL_CreateGPUSampler(self.device, ctypes.byref(info)),
            "SDL_CreateGPUSampler",
        )
        return self.samplers.add(Sampler(handle, descriptor))

    def get_sampler(self, handle: SamplerHandle) -> Sampler:
        return self.samplers.get(handle)

    def destroy_sampler(self, handle: SamplerHandle) -> None:
        sampler = self.samplers.remove(handle)
        sdl.SDL_ReleaseGPUSampler(self.device, sampler.handle)

    def create_shader(self, descriptor: ShaderDescriptor) -> ShaderHandle:
        info, keep_alive = descriptor.to_sdl()
        handle = check(
            sdl.SDL_CreateGPUShader(self.device, ctypes.byref(info)),
            "SDL_CreateGPUShader",
        )
        keep_alive.clear()
        return self.shaders.add(Shader(handle, descriptor))

    def get_shader(self, handle: ShaderHandle) -> Shader:
        return self.shaders.get(handle)

    def destroy_shader(self, handle: ShaderHandle) -> None:
        shader = self.shaders.remove(handle)
        sdl.SDL_ReleaseGPUShader(self.device, shader.handle)

    def create_transfer_buffer(
        self,
        descriptor: TransferBufferDescriptor,
    ) -> TransferBufferHandle:
        info = descriptor.to_sdl()
        handle = check(
            sdl.SDL_CreateGPUTransferBuffer(self.device, ctypes.byref(info)),
            "SDL_CreateGPUTransferBuffer",
        )
        return self.transfer_buffers.add(TransferBuffer(handle, descriptor))

    def get_transfer_buffer(self, handle: TransferBufferHandle) -> TransferBuffer:
        return self.transfer_buffers.get(handle)

    def destroy_transfer_buffer(self, handle: TransferBufferHandle) -> None:
        transfer_buffer = self.transfer_buffers.remove(handle)
        sdl.SDL_ReleaseGPUTransferBuffer(self.device, transfer_buffer.handle)

    def create_graphics_pipeline(
        self,
        descriptor: GraphicsPipelineDescriptor,
    ) -> GraphicsPipelineHandle:
        vertex_shader = self._shader_handle(descriptor.vertex_shader)
        fragment_shader = self._shader_handle(descriptor.fragment_shader)
        info, keep_alive = descriptor.to_sdl(vertex_shader, fragment_shader)
        handle = check(
            sdl.SDL_CreateGPUGraphicsPipeline(self.device, ctypes.byref(info)),
            "SDL_CreateGPUGraphicsPipeline",
        )
        keep_alive.clear()
        return self.graphics_pipelines.add(GraphicsPipeline(handle, descriptor))

    def get_graphics_pipeline(
        self,
        handle: GraphicsPipelineHandle,
    ) -> GraphicsPipeline:
        return self.graphics_pipelines.get(handle)

    def destroy_graphics_pipeline(self, handle: GraphicsPipelineHandle) -> None:
        pipeline = self.graphics_pipelines.remove(handle)
        sdl.SDL_ReleaseGPUGraphicsPipeline(self.device, pipeline.handle)

    def create_compute_pipeline(
        self,
        descriptor: ComputePipelineDescriptor,
    ) -> ComputePipelineHandle:
        info, keep_alive = descriptor.to_sdl()
        handle = check(
            sdl.SDL_CreateGPUComputePipeline(self.device, ctypes.byref(info)),
            "SDL_CreateGPUComputePipeline",
        )
        keep_alive.clear()
        return self.compute_pipelines.add(ComputePipeline(handle, descriptor))

    def get_compute_pipeline(self, handle: ComputePipelineHandle) -> ComputePipeline:
        return self.compute_pipelines.get(handle)

    def destroy_compute_pipeline(self, handle: ComputePipelineHandle) -> None:
        pipeline = self.compute_pipelines.remove(handle)
        sdl.SDL_ReleaseGPUComputePipeline(self.device, pipeline.handle)

    def create_bind_group_layout(
        self,
        descriptor: BindGroupLayoutDescriptor,
    ) -> BindGroupLayoutHandle:
        return self.bind_group_layouts.add(BindGroupLayout(descriptor))

    def get_bind_group_layout(
        self,
        handle: BindGroupLayoutHandle,
    ) -> BindGroupLayout:
        return self.bind_group_layouts.get(handle)

    def destroy_bind_group_layout(self, handle: BindGroupLayoutHandle) -> None:
        self.bind_group_layouts.remove(handle)

    def create_bind_group(self, descriptor: BindGroupDescriptor) -> BindGroupHandle:
        if isinstance(descriptor.layout, PoolHandle):
            self.bind_group_layouts.get(descriptor.layout)
        return self.bind_groups.add(BindGroup(descriptor))

    def get_bind_group(self, handle: BindGroupHandle) -> BindGroup:
        return self.bind_groups.get(handle)

    def destroy_bind_group(self, handle: BindGroupHandle) -> None:
        self.bind_groups.remove(handle)

    def create_render_state(
        self,
        renderer: Any,
        descriptor: RenderStateDescriptor,
    ) -> RenderStateHandle:
        fragment_shader = self._shader_handle(descriptor.fragment_shader)
        sampler_bindings = [
            (
                self._texture_handle(binding.texture),
                self._sampler_handle(binding.sampler),
            )
            for binding in descriptor.sampler_bindings
        ]
        storage_textures = [
            self._texture_handle(texture) for texture in descriptor.storage_textures
        ]
        storage_buffers = [
            self._buffer_handle(buffer) for buffer in descriptor.storage_buffers
        ]
        info, keep_alive = descriptor.to_sdl(
            fragment_shader,
            sampler_bindings,
            storage_textures,
            storage_buffers,
        )
        renderer_handle = getattr(renderer, "raw", getattr(renderer, "handle", renderer))
        handle = check(
            sdl.SDL_CreateGPURenderState(renderer_handle, ctypes.byref(info)),
            "SDL_CreateGPURenderState",
        )
        keep_alive.clear()
        return self.render_states.add(RenderState(handle, descriptor))

    def get_render_state(self, handle: RenderStateHandle) -> RenderState:
        return self.render_states.get(handle)

    def destroy_render_state(self, handle: RenderStateHandle) -> None:
        render_state = self.render_states.remove(handle)
        sdl.SDL_DestroyGPURenderState(render_state.handle)

    def close(self) -> None:
        for handle in reversed(self.render_states.handles()):
            self.destroy_render_state(handle)
        for handle in reversed(self.bind_groups.handles()):
            self.destroy_bind_group(handle)
        for handle in reversed(self.bind_group_layouts.handles()):
            self.destroy_bind_group_layout(handle)
        for handle in reversed(self.compute_pipelines.handles()):
            self.destroy_compute_pipeline(handle)
        for handle in reversed(self.graphics_pipelines.handles()):
            self.destroy_graphics_pipeline(handle)
        for handle in reversed(self.transfer_buffers.handles()):
            self.destroy_transfer_buffer(handle)
        for handle in reversed(self.samplers.handles()):
            self.destroy_sampler(handle)
        for handle in reversed(self.textures.handles()):
            self.destroy_texture(handle)
        for handle in reversed(self.buffers.handles()):
            self.destroy_buffer(handle)
        for handle in reversed(self.shaders.handles()):
            self.destroy_shader(handle)

    def _shader_handle(self, value: ShaderHandle | Any | None):
        if value is None:
            return None
        if isinstance(value, PoolHandle):
            return self.shaders.get(value).handle
        return value

    def _texture_handle(self, value: TextureHandle | Any):
        if isinstance(value, PoolHandle):
            return self.textures.get(value).handle
        return value

    def _buffer_handle(self, value: BufferHandle | Any):
        if isinstance(value, PoolHandle):
            return self.buffers.get(value).handle
        return value

    def _sampler_handle(self, value: SamplerHandle | Any):
        if isinstance(value, PoolHandle):
            return self.samplers.get(value).handle
        return value

    @staticmethod
    def _payload_bytes(data: Any) -> bytes:
        if isinstance(data, bytes):
            return data
        if isinstance(data, bytearray):
            return bytes(data)
        if isinstance(data, memoryview):
            return data.tobytes()
        if hasattr(data, "tobytes"):
            return data.tobytes()
        return bytes(data)

    def __enter__(self) -> "ResourceManager":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
