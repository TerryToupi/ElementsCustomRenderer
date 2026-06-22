from __future__ import annotations

import ctypes
from dataclasses import dataclass
from typing import Any, Sequence

from ._sdl import sdl

from .CommandBuffer import CommandBuffer, RecordedRenderPass
from .Enums import IndexElementSize, LoadOp, ShaderFormat, StoreOp, to_sdl
from .Errors import RendererError
from .Utils.Sdl import check, to_bytes


@dataclass
class GpuRenderPassDesc:
    surface: Any
    clear_color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    load_op: LoadOp | int = LoadOp.CLEAR
    store_op: StoreOp | int = StoreOp.STORE
    depth_texture: Any | None = None
    clear_depth: float = 1.0
    depth_load_op: LoadOp | int = LoadOp.CLEAR
    depth_store_op: StoreOp | int = StoreOp.DONT_CARE


class Device:
    def __init__(
        self,
        shader_formats: ShaderFormat | int = ShaderFormat.SPIRV,
        debug_mode: bool = True,
        driver_name: str | bytes | None = None,
    ):
        self.handle = None
        self.command_buffer: CommandBuffer | None = None
        self.render_pass = None
        self.compute_pass = None
        self.handle = check(
            sdl.SDL_CreateGPUDevice(
                to_sdl(shader_formats),
                debug_mode,
                to_bytes(driver_name),
            ),
            "SDL_CreateGPUDevice",
        )

    @property
    def raw(self):
        if self.handle is None:
            raise RuntimeError("device is closed")
        return self.handle

    def claim_window(self, window: Any) -> None:
        window_handle = getattr(window, "raw", getattr(window, "handle", window))
        check(
            sdl.SDL_ClaimWindowForGPUDevice(self.raw, window_handle),
            "SDL_ClaimWindowForGPUDevice",
        )

    def release_window(self, window: Any) -> None:
        if self.handle is None:
            return

        window_handle = getattr(window, "raw", getattr(window, "handle", window))
        if window_handle:
            sdl.SDL_ReleaseWindowFromGPUDevice(self.handle, window_handle)

    def acquire_command_buffer(self):
        if self.command_buffer is not None:
            return self.command_buffer

        self.command_buffer = CommandBuffer(self)
        return self.command_buffer

    def current_command_buffer(self) -> CommandBuffer:
        if self.command_buffer is None:
            raise RendererError("device has no active command buffer")
        return self.command_buffer

    def cancel_command_buffer(self, command_buffer: CommandBuffer | None = None) -> None:
        command_buffer = command_buffer or self.command_buffer
        if command_buffer is None:
            return
        command_buffer._mark_cancelled()
        if command_buffer == self.command_buffer:
            self.command_buffer = None

    def submit_command_buffer(self, command_buffer: CommandBuffer | None = None) -> None:
        command_buffer = command_buffer or self.current_command_buffer()
        command_buffer.mark_submitted()

        try:
            sdl_command_buffer = check(
                sdl.SDL_AcquireGPUCommandBuffer(self.raw),
                "SDL_AcquireGPUCommandBuffer",
            )
        except Exception:
            command_buffer._mark_cancelled()
            if command_buffer == self.command_buffer:
                self.command_buffer = None
            raise

        try:
            self._replay_command_buffer(command_buffer, sdl_command_buffer)
        except Exception:
            self.render_pass = None
            self.compute_pass = None
            command_buffer._mark_cancelled()
            if command_buffer == self.command_buffer:
                self.command_buffer = None
            sdl.SDL_CancelGPUCommandBuffer(sdl_command_buffer)
            raise

        try:
            check(
                sdl.SDL_SubmitGPUCommandBuffer(sdl_command_buffer),
                "SDL_SubmitGPUCommandBuffer",
            )
        finally:
            if command_buffer == self.command_buffer:
                self.command_buffer = None

    def acquire_surface_image(self, surface: Any):
        return self.current_command_buffer().acquire_surface_image(surface)

    def begin_compute_pass(
        self,
        storage_buffers: Sequence[Any] = (),
    ):
        return self.current_command_buffer().begin_compute_pass(storage_buffers)

    def end_compute_pass(self) -> None:
        self.current_command_buffer().end_compute_pass()

    def gpu_dispatch(
        self,
        data_gpu: Any | None,
        grid_dimensions: tuple[int, int, int],
    ) -> None:
        self.current_command_buffer().gpu_dispatch(data_gpu, grid_dimensions)

    def gpu_dispatch_indirect(
        self,
        data_gpu: Any | None,
        grid_dimensions_gpu: Any,
    ) -> None:
        self.current_command_buffer().gpu_dispatch_indirect(
            data_gpu,
            grid_dimensions_gpu,
        )

    def gpu_begin_render_pass(self, desc: GpuRenderPassDesc):
        return self.current_command_buffer().begin_render_pass(desc)

    def gpu_end_render_pass(self) -> None:
        self.current_command_buffer().end_render_pass()

    def gpu_draw_indexed_instanced(
        self,
        vertex_data_gpu: Any | None,
        pixel_data_gpu: Any | None,
        indices_gpu: Any,
        index_count: int,
        instance_count: int,
        *,
        index_element_size: IndexElementSize | int = IndexElementSize.BIT32,
        first_index: int = 0,
        vertex_offset: int = 0,
        first_instance: int = 0,
    ) -> None:
        self.current_command_buffer().gpu_draw_indexed_instanced(
            vertex_data_gpu,
            pixel_data_gpu,
            indices_gpu,
            index_count,
            instance_count,
            index_element_size=index_element_size,
            first_index=first_index,
            vertex_offset=vertex_offset,
            first_instance=first_instance,
        )

    def gpu_draw_indexed_instanced_indirect(
        self,
        vertex_data_gpu: Any | None,
        pixel_data_gpu: Any | None,
        indices_gpu: Any,
        args_gpu: Any,
        *,
        index_element_size: IndexElementSize | int = IndexElementSize.BIT32,
        draw_count: int = 1,
    ) -> None:
        self.current_command_buffer().gpu_draw_indexed_instanced_indirect(
            vertex_data_gpu,
            pixel_data_gpu,
            indices_gpu,
            args_gpu,
            index_element_size=index_element_size,
            draw_count=draw_count,
        )

    def gpu_draw_indexed_instanced_indirect_multi(
        self,
        data_vx_gpu: Any | None,
        vx_stride: int,
        data_px_gpu: Any | None,
        px_stride: int,
        args_gpu: Any,
        draw_count_gpu: Any,
    ) -> None:
        self.current_command_buffer().gpu_draw_indexed_instanced_indirect_multi(
            data_vx_gpu,
            vx_stride,
            data_px_gpu,
            px_stride,
            args_gpu,
            draw_count_gpu,
        )

    gpuDispatch = gpu_dispatch
    gpuDispatchIndirect = gpu_dispatch_indirect
    gpuBeginRenderPass = gpu_begin_render_pass
    gpuEndRenderPass = gpu_end_render_pass
    gpuDrawIndexedInstanced = gpu_draw_indexed_instanced
    gpuDrawIndexedInstancedIndirect = gpu_draw_indexed_instanced_indirect
    gpuDrawIndexedInstancedIndirectMulti = gpu_draw_indexed_instanced_indirect_multi

    def bind_graphics_pipeline(
        self,
        render_pass_or_pipeline: Any,
        pipeline: Any | None = None,
    ) -> None:
        self.current_command_buffer().bind_graphics_pipeline(
            render_pass_or_pipeline,
            pipeline,
        )

    def bind_vertex_buffers(
        self,
        bindings: Sequence[Any],
        first_slot: int = 0,
    ) -> None:
        self.current_command_buffer().bind_vertex_buffers(bindings, first_slot)

    def push_vertex_uniform_data(
        self,
        slot_index: int,
        data: bytes | bytearray | memoryview,
    ) -> None:
        self.current_command_buffer().push_vertex_uniform_data(slot_index, data)

    def push_fragment_uniform_data(
        self,
        slot_index: int,
        data: bytes | bytearray | memoryview,
    ) -> None:
        self.current_command_buffer().push_fragment_uniform_data(slot_index, data)

    def draw_primitives(
        self,
        render_pass_or_vertex_count: Any,
        vertex_count: int | None = None,
        instance_count: int = 1,
        first_vertex: int = 0,
        first_instance: int = 0,
    ) -> None:
        self.current_command_buffer().draw_primitives(
            render_pass_or_vertex_count,
            vertex_count,
            instance_count,
            first_vertex,
            first_instance,
        )

    @staticmethod
    def end_render_pass(render_pass: Any) -> None:
        if isinstance(render_pass, RecordedRenderPass):
            render_pass.command_buffer.end_render_pass()
            return
        sdl.SDL_EndGPURenderPass(render_pass)

    def current_render_pass(self):
        return self.current_command_buffer().current_render_pass()

    def _replay_command_buffer(
        self,
        command_buffer: CommandBuffer,
        sdl_command_buffer: Any,
    ) -> None:
        skip_render_pass = False
        self.render_pass = None
        self.compute_pass = None

        for command in command_buffer.commands:
            if command.name == "acquire_surface_image":
                surface = command.args[0]
                surface.acquire(sdl_command_buffer)
            elif command.name == "begin_compute_pass":
                self.compute_pass = self._begin_compute_pass_raw(
                    sdl_command_buffer,
                    command.args[0],
                )
            elif command.name == "end_compute_pass":
                self._end_compute_pass_raw()
            elif command.name == "dispatch":
                self._dispatch_raw(*command.args)
            elif command.name == "dispatch_indirect":
                self._dispatch_indirect_raw(*command.args)
            elif command.name == "begin_render_pass":
                desc = command.args[0]
                if desc.surface.current_image is None:
                    skip_render_pass = True
                    self.render_pass = None
                    continue
                self.render_pass = desc.surface.begin_render_pass(
                    sdl_command_buffer,
                    clear_color=desc.clear_color,
                    load_op=desc.load_op,
                    store_op=desc.store_op,
                    depth_texture=desc.depth_texture,
                    clear_depth=desc.clear_depth,
                    depth_load_op=desc.depth_load_op,
                    depth_store_op=desc.depth_store_op,
                )
            elif command.name == "end_render_pass":
                if skip_render_pass:
                    skip_render_pass = False
                    continue
                self._end_render_pass_raw()
            elif skip_render_pass:
                continue
            elif command.name == "draw_indexed_instanced":
                self._draw_indexed_instanced_raw(*command.args)
            elif command.name == "draw_indexed_instanced_indirect":
                self._draw_indexed_instanced_indirect_raw(*command.args)
            elif command.name == "draw_indexed_instanced_indirect_multi":
                self._draw_indexed_instanced_indirect_multi_raw(*command.args)
            elif command.name == "bind_graphics_pipeline":
                self._bind_graphics_pipeline_raw(*command.args)
            elif command.name == "bind_vertex_buffers":
                self._bind_vertex_buffers_raw(*command.args)
            elif command.name == "push_vertex_uniform_data":
                self._push_vertex_uniform_data_raw(sdl_command_buffer, *command.args)
            elif command.name == "push_fragment_uniform_data":
                self._push_fragment_uniform_data_raw(sdl_command_buffer, *command.args)
            elif command.name == "draw_primitives":
                self._draw_primitives_raw(*command.args)
            else:
                raise RendererError(f"unknown command buffer command: {command.name}")

        self.render_pass = None
        self.compute_pass = None

    def _begin_compute_pass_raw(
        self,
        sdl_command_buffer: Any,
        storage_buffers: Sequence[Any] = (),
    ):
        if self.compute_pass is not None:
            return self.compute_pass
        if self.render_pass is not None:
            raise RendererError("cannot begin a compute pass inside a render pass")

        bindings = None
        binding_count = 0
        keep_alive: list[Any] = []
        if storage_buffers:
            bindings = (sdl.SDL_GPUStorageBufferReadWriteBinding * len(storage_buffers))()
            for index, buffer in enumerate(storage_buffers):
                bindings[index].buffer = self._raw_handle(buffer)
                bindings[index].cycle = False
            binding_count = len(storage_buffers)
            keep_alive.append(bindings)

        return check(
            sdl.SDL_BeginGPUComputePass(
                sdl_command_buffer,
                None,
                0,
                bindings,
                binding_count,
            ),
            "SDL_BeginGPUComputePass",
        )

    def _end_compute_pass_raw(self) -> None:
        if self.compute_pass is None:
            return
        sdl.SDL_EndGPUComputePass(self.compute_pass)
        self.compute_pass = None

    def _dispatch_raw(
        self,
        data_gpu: Any | None,
        grid_dimensions: tuple[int, int, int],
    ) -> None:
        compute_pass = self._current_compute_pass_raw()
        if data_gpu is not None:
            self._bind_compute_storage_buffers(compute_pass, 0, (data_gpu,))
        sdl.SDL_DispatchGPUCompute(
            compute_pass,
            grid_dimensions[0],
            grid_dimensions[1],
            grid_dimensions[2],
        )

    def _dispatch_indirect_raw(
        self,
        data_gpu: Any | None,
        grid_dimensions_gpu: Any,
    ) -> None:
        compute_pass = self._current_compute_pass_raw()
        if data_gpu is not None:
            self._bind_compute_storage_buffers(compute_pass, 0, (data_gpu,))
        buffer, offset = self._buffer_and_offset(grid_dimensions_gpu)
        sdl.SDL_DispatchGPUComputeIndirect(compute_pass, buffer, offset)

    def _end_render_pass_raw(self) -> None:
        if self.render_pass is None:
            return
        sdl.SDL_EndGPURenderPass(self.render_pass)
        self.render_pass = None

    def _draw_indexed_instanced_raw(
        self,
        vertex_data_gpu: Any | None,
        pixel_data_gpu: Any | None,
        indices_gpu: Any,
        index_count: int,
        instance_count: int,
        index_element_size: IndexElementSize | int,
        first_index: int,
        vertex_offset: int,
        first_instance: int,
    ) -> None:
        render_pass = self._current_render_pass_raw()
        self._bind_draw_data(render_pass, vertex_data_gpu, pixel_data_gpu)
        self._bind_index_buffer(render_pass, indices_gpu, index_element_size)
        sdl.SDL_DrawGPUIndexedPrimitives(
            render_pass,
            index_count,
            instance_count,
            first_index,
            vertex_offset,
            first_instance,
        )

    def _draw_indexed_instanced_indirect_raw(
        self,
        vertex_data_gpu: Any | None,
        pixel_data_gpu: Any | None,
        indices_gpu: Any,
        args_gpu: Any,
        index_element_size: IndexElementSize | int,
        draw_count: int,
    ) -> None:
        render_pass = self._current_render_pass_raw()
        self._bind_draw_data(render_pass, vertex_data_gpu, pixel_data_gpu)
        self._bind_index_buffer(render_pass, indices_gpu, index_element_size)
        buffer, offset = self._buffer_and_offset(args_gpu)
        sdl.SDL_DrawGPUIndexedPrimitivesIndirect(
            render_pass,
            buffer,
            offset,
            draw_count,
        )

    def _draw_indexed_instanced_indirect_multi_raw(
        self,
        data_vx_gpu: Any | None,
        data_px_gpu: Any | None,
        args_gpu: Any,
        draw_count_gpu: int,
    ) -> None:
        render_pass = self._current_render_pass_raw()
        self._bind_draw_data(render_pass, data_vx_gpu, data_px_gpu)
        buffer, offset = self._buffer_and_offset(args_gpu)
        sdl.SDL_DrawGPUIndexedPrimitivesIndirect(
            render_pass,
            buffer,
            offset,
            draw_count_gpu,
        )

    def _bind_graphics_pipeline_raw(self, pipeline: Any) -> None:
        render_pass = self._current_render_pass_raw()
        pipeline_handle = getattr(pipeline, "raw", getattr(pipeline, "handle", pipeline))
        sdl.SDL_BindGPUGraphicsPipeline(render_pass, pipeline_handle)

    def _bind_vertex_buffers_raw(
        self,
        bindings: Sequence[Any],
        first_slot: int = 0,
    ) -> None:
        render_pass = self._current_render_pass_raw()
        sdl_bindings = (sdl.SDL_GPUBufferBinding * len(bindings))()
        for index, binding_value in enumerate(bindings):
            buffer, offset = self._buffer_and_offset(binding_value)
            sdl_bindings[index].buffer = buffer
            sdl_bindings[index].offset = offset
        sdl.SDL_BindGPUVertexBuffers(
            render_pass,
            first_slot,
            sdl_bindings,
            len(bindings),
        )

    @staticmethod
    def _push_vertex_uniform_data_raw(
        sdl_command_buffer: Any,
        slot_index: int,
        data: bytes,
    ) -> None:
        payload = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
        sdl.SDL_PushGPUVertexUniformData(
            sdl_command_buffer,
            slot_index,
            ctypes.cast(payload, ctypes.c_void_p),
            len(data),
        )

    @staticmethod
    def _push_fragment_uniform_data_raw(
        sdl_command_buffer: Any,
        slot_index: int,
        data: bytes,
    ) -> None:
        payload = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
        sdl.SDL_PushGPUFragmentUniformData(
            sdl_command_buffer,
            slot_index,
            ctypes.cast(payload, ctypes.c_void_p),
            len(data),
        )

    def _draw_primitives_raw(
        self,
        vertex_count: int,
        instance_count: int = 1,
        first_vertex: int = 0,
        first_instance: int = 0,
    ) -> None:
        sdl.SDL_DrawGPUPrimitives(
            self._current_render_pass_raw(),
            vertex_count,
            instance_count,
            first_vertex,
            first_instance,
        )

    def _current_render_pass_raw(self):
        if self.render_pass is None:
            raise RendererError("device has no active render pass")
        return self.render_pass

    def _current_compute_pass_raw(self):
        if self.compute_pass is None:
            raise RendererError("device has no active compute pass")
        return self.compute_pass

    def _bind_draw_data(
        self,
        render_pass: Any,
        vertex_data_gpu: Any | None,
        pixel_data_gpu: Any | None,
    ) -> None:
        if vertex_data_gpu is not None:
            self._bind_vertex_storage_buffers(render_pass, 0, (vertex_data_gpu,))
        if pixel_data_gpu is not None:
            self._bind_fragment_storage_buffers(render_pass, 0, (pixel_data_gpu,))

    def _bind_index_buffer(
        self,
        render_pass: Any,
        indices_gpu: Any,
        index_element_size: IndexElementSize | int,
    ) -> None:
        buffer, offset = self._buffer_and_offset(indices_gpu)
        binding = sdl.SDL_GPUBufferBinding()
        binding.buffer = buffer
        binding.offset = offset
        sdl.SDL_BindGPUIndexBuffer(
            render_pass,
            ctypes.byref(binding),
            to_sdl(index_element_size),
        )

    def _bind_compute_storage_buffers(
        self,
        compute_pass: Any,
        first_slot: int,
        buffers: Sequence[Any],
    ) -> None:
        buffer_array = self._buffer_array(buffers)
        sdl.SDL_BindGPUComputeStorageBuffers(
            compute_pass,
            first_slot,
            buffer_array,
            len(buffers),
        )

    def _bind_vertex_storage_buffers(
        self,
        render_pass: Any,
        first_slot: int,
        buffers: Sequence[Any],
    ) -> None:
        buffer_array = self._buffer_array(buffers)
        sdl.SDL_BindGPUVertexStorageBuffers(
            render_pass,
            first_slot,
            buffer_array,
            len(buffers),
        )

    def _bind_fragment_storage_buffers(
        self,
        render_pass: Any,
        first_slot: int,
        buffers: Sequence[Any],
    ) -> None:
        buffer_array = self._buffer_array(buffers)
        sdl.SDL_BindGPUFragmentStorageBuffers(
            render_pass,
            first_slot,
            buffer_array,
            len(buffers),
        )

    def _buffer_array(self, buffers: Sequence[Any]):
        buffer_type = ctypes.POINTER(sdl.SDL_GPUBuffer) * len(buffers)
        return buffer_type(*(self._buffer_and_offset(buffer)[0] for buffer in buffers))

    def _buffer_and_offset(self, value: Any) -> tuple[Any, int]:
        if isinstance(value, tuple):
            buffer, offset = value
            return self._raw_handle(buffer), int(offset)
        return self._raw_handle(value), 0

    @staticmethod
    def _raw_handle(value: Any):
        return getattr(value, "raw", getattr(value, "handle", value))

    def close(self) -> None:
        if self.command_buffer is not None:
            self.cancel_command_buffer()
        if self.handle is not None:
            sdl.SDL_DestroyGPUDevice(self.handle)
            self.handle = None

    def __enter__(self) -> "Device":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
