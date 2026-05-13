from __future__ import annotations

from typing import Any

import sdl3 as sdl

from Enums import ShaderFormat, to_sdl
from Utils.Sdl import check, to_bytes


class Device:
    def __init__(
        self,
        shader_formats: ShaderFormat | int = ShaderFormat.SPIRV,
        debug_mode: bool = True,
        driver_name: str | bytes | None = None,
    ):
        self.handle = None
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
        return check(
            sdl.SDL_AcquireGPUCommandBuffer(self.raw),
            "SDL_AcquireGPUCommandBuffer",
        )

    def cancel_command_buffer(self, command_buffer: Any) -> None:
        sdl.SDL_CancelGPUCommandBuffer(command_buffer)

    def submit_command_buffer(self, command_buffer: Any) -> None:
        check(
            sdl.SDL_SubmitGPUCommandBuffer(command_buffer),
            "SDL_SubmitGPUCommandBuffer",
        )

    @staticmethod
    def bind_graphics_pipeline(render_pass: Any, pipeline: Any) -> None:
        pipeline_handle = getattr(pipeline, "raw", getattr(pipeline, "handle", pipeline))
        sdl.SDL_BindGPUGraphicsPipeline(render_pass, pipeline_handle)

    @staticmethod
    def draw_primitives(
        render_pass: Any,
        vertex_count: int,
        instance_count: int = 1,
        first_vertex: int = 0,
        first_instance: int = 0,
    ) -> None:
        sdl.SDL_DrawGPUPrimitives(
            render_pass,
            vertex_count,
            instance_count,
            first_vertex,
            first_instance,
        )

    @staticmethod
    def end_render_pass(render_pass: Any) -> None:
        sdl.SDL_EndGPURenderPass(render_pass)

    def close(self) -> None:
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
