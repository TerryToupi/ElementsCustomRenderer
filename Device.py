from __future__ import annotations

from typing import Any

import sdl3 as sdl

from Utils.Sdl import check, to_bytes


class Device:
    def __init__(
        self,
        shader_formats: int = sdl.SDL_GPU_SHADERFORMAT_SPIRV,
        debug_mode: bool = True,
        driver_name: str | bytes | None = None,
    ):
        self.handle = None
        self.handle = check(
            sdl.SDL_CreateGPUDevice(
                shader_formats,
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
