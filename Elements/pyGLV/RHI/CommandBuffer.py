from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from .Enums import IndexElementSize
from .Errors import RendererError


@dataclass(frozen=True)
class RecordedCommand:
    name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


@dataclass(frozen=True)
class RecordedSurfaceImage:
    surface: Any


@dataclass(frozen=True)
class RecordedRenderPass:
    command_buffer: "CommandBuffer"


@dataclass(frozen=True)
class RecordedComputePass:
    command_buffer: "CommandBuffer"


class CommandBuffer:
    def __init__(self, device: Any):
        self.device = device
        self.commands: list[RecordedCommand] = []
        self.render_pass: RecordedRenderPass | None = None
        self.compute_pass: RecordedComputePass | None = None
        self.submitted = False
        self.cancelled = False

    def record(self, name: str, *args: Any, **kwargs: Any) -> None:
        self._ensure_recording()
        self.commands.append(RecordedCommand(name, args, kwargs))

    def acquire_surface_image(self, surface: Any) -> RecordedSurfaceImage:
        self.record("acquire_surface_image", surface)
        return RecordedSurfaceImage(surface)

    def begin_compute_pass(
        self,
        storage_buffers: Sequence[Any] = (),
    ) -> RecordedComputePass:
        self._ensure_recording()
        if self.compute_pass is not None:
            return self.compute_pass
        if self.render_pass is not None:
            raise RendererError("cannot begin a compute pass inside a render pass")

        self.compute_pass = RecordedComputePass(self)
        self.record("begin_compute_pass", tuple(storage_buffers))
        return self.compute_pass

    def end_compute_pass(self) -> None:
        if self.compute_pass is None:
            return
        self.record("end_compute_pass")
        self.compute_pass = None

    def begin_render_pass(self, desc: Any) -> RecordedRenderPass:
        self._ensure_recording()
        if self.render_pass is not None:
            return self.render_pass
        if self.compute_pass is not None:
            raise RendererError("cannot begin a render pass inside a compute pass")

        self.render_pass = RecordedRenderPass(self)
        self.record("begin_render_pass", desc)
        return self.render_pass

    def end_render_pass(self) -> None:
        if self.render_pass is None:
            return
        self.record("end_render_pass")
        self.render_pass = None

    def gpu_dispatch(
        self,
        data_gpu: Any | None,
        grid_dimensions: tuple[int, int, int],
    ) -> None:
        self._compute_pass_or_begin()
        self.record("dispatch", data_gpu, grid_dimensions)

    def gpu_dispatch_indirect(
        self,
        data_gpu: Any | None,
        grid_dimensions_gpu: Any,
    ) -> None:
        self._compute_pass_or_begin()
        self.record("dispatch_indirect", data_gpu, grid_dimensions_gpu)

    gpuDispatch = gpu_dispatch
    gpuDispatchIndirect = gpu_dispatch_indirect
    gpuBeginRenderPass = begin_render_pass
    gpuEndRenderPass = end_render_pass

    def bind_compute_pipeline(
        self,
        compute_pass_or_pipeline: Any,
        pipeline: Any | None = None,
    ) -> None:
        # Compute work is explicit: begin a compute pass, bind one compute
        # pipeline, then dispatch workgroups.
        if pipeline is None:
            pipeline = compute_pass_or_pipeline
        else:
            self._validate_recorded_compute_pass(compute_pass_or_pipeline)
        self.current_compute_pass()
        self.record("bind_compute_pipeline", pipeline)

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
        self.current_render_pass()
        self.record(
            "draw_indexed_instanced",
            vertex_data_gpu,
            pixel_data_gpu,
            indices_gpu,
            index_count,
            instance_count,
            index_element_size,
            first_index,
            vertex_offset,
            first_instance,
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
        self.current_render_pass()
        self.record(
            "draw_indexed_instanced_indirect",
            vertex_data_gpu,
            pixel_data_gpu,
            indices_gpu,
            args_gpu,
            index_element_size,
            draw_count,
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
        if not isinstance(draw_count_gpu, int):
            raise RendererError(
                "SDL_DrawGPUIndexedPrimitivesIndirect requires a CPU draw_count; "
                "this SDL binding does not expose GPU draw-count indirect multi"
            )

        self.current_render_pass()
        self.record(
            "draw_indexed_instanced_indirect_multi",
            self._buffer_with_stride(data_vx_gpu, vx_stride),
            self._buffer_with_stride(data_px_gpu, px_stride),
            args_gpu,
            draw_count_gpu,
        )

    gpuDrawIndexedInstanced = gpu_draw_indexed_instanced
    gpuDrawIndexedInstancedIndirect = gpu_draw_indexed_instanced_indirect
    gpuDrawIndexedInstancedIndirectMulti = gpu_draw_indexed_instanced_indirect_multi

    def bind_graphics_pipeline(
        self,
        render_pass_or_pipeline: Any,
        pipeline: Any | None = None,
    ) -> None:
        if pipeline is None:
            pipeline = render_pass_or_pipeline
        else:
            self._validate_recorded_render_pass(render_pass_or_pipeline)
        self.current_render_pass()
        self.record("bind_graphics_pipeline", pipeline)

    def bind_vertex_buffers(
        self,
        bindings: Sequence[Any],
        first_slot: int = 0,
    ) -> None:
        self.current_render_pass()
        self.record("bind_vertex_buffers", tuple(bindings), first_slot)

    def push_vertex_uniform_data(
        self,
        slot_index: int,
        data: bytes | bytearray | memoryview,
    ) -> None:
        self.current_render_pass()
        self.record("push_vertex_uniform_data", slot_index, bytes(data))

    def push_fragment_uniform_data(
        self,
        slot_index: int,
        data: bytes | bytearray | memoryview,
    ) -> None:
        self.current_render_pass()
        self.record("push_fragment_uniform_data", slot_index, bytes(data))

    def draw_primitives(
        self,
        render_pass_or_vertex_count: Any,
        vertex_count: int | None = None,
        instance_count: int = 1,
        first_vertex: int = 0,
        first_instance: int = 0,
    ) -> None:
        if vertex_count is None:
            vertex_count = render_pass_or_vertex_count
        else:
            self._validate_recorded_render_pass(render_pass_or_vertex_count)
        self.current_render_pass()
        self.record(
            "draw_primitives",
            vertex_count,
            instance_count,
            first_vertex,
            first_instance,
        )

    def current_render_pass(self) -> RecordedRenderPass:
        if self.render_pass is None:
            raise RendererError("command buffer has no active render pass")
        return self.render_pass

    def current_compute_pass(self) -> RecordedComputePass:
        if self.compute_pass is None:
            raise RendererError("command buffer has no active compute pass")
        return self.compute_pass

    def mark_submitted(self) -> None:
        self._ensure_recording()
        if self.render_pass is not None:
            raise RendererError("cannot submit while a render pass is active")
        if self.compute_pass is not None:
            raise RendererError("cannot submit while a compute pass is active")
        self.submitted = True

    def submit(self) -> None:
        self.device.submit_command_buffer(self)

    def cancel(self) -> None:
        self.device.cancel_command_buffer(self)

    def _mark_cancelled(self) -> None:
        self.render_pass = None
        self.compute_pass = None
        self.cancelled = True

    def _ensure_recording(self) -> None:
        if self.cancelled:
            raise RendererError("cannot record into a cancelled command buffer")
        if self.submitted:
            raise RendererError("cannot record into a submitted command buffer")

    def _compute_pass_or_begin(self) -> RecordedComputePass:
        if self.compute_pass is not None:
            return self.compute_pass
        return self.begin_compute_pass()

    def _validate_recorded_render_pass(self, render_pass: Any) -> None:
        if (
            not isinstance(render_pass, RecordedRenderPass)
            or render_pass.command_buffer != self
        ):
            raise RendererError("render pass must belong to this command buffer")

    def _validate_recorded_compute_pass(self, compute_pass: Any) -> None:
        # This catches accidental mixing of command buffers in teaching examples.
        if (
            not isinstance(compute_pass, RecordedComputePass)
            or compute_pass.command_buffer != self
        ):
            raise RendererError("compute pass must belong to this command buffer")

    @staticmethod
    def _buffer_with_stride(value: Any | None, stride: int):
        if value is None:
            return None
        if isinstance(value, tuple):
            buffer, offset = value
            return buffer, offset
        return value
