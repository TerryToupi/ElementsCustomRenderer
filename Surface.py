from __future__ import annotations

import ctypes
from dataclasses import dataclass
from typing import Any

import sdl3 as sdl

from Enums import (
    LoadOp,
    PresentMode,
    StoreOp,
    SwapchainComposition,
    TextureFormat,
    from_sdl,
    to_sdl,
)
from Utils.Sdl import SdlError, check, error_message


@dataclass(slots=True)
class SurfaceDescriptor:
    composition: SwapchainComposition | int = SwapchainComposition.SDR
    present_mode: PresentMode | int = PresentMode.MAILBOX
    image_count: int = 3


@dataclass(slots=True)
class SurfaceImage:
    texture: Any
    width: int
    height: int
    format: TextureFormat | int
    slot: int
    frame_number: int


class Surface:
    def __init__(
        self,
        device: Any,
        window: Any,
        descriptor: SurfaceDescriptor | None = None,
    ):
        self.device = getattr(device, "raw", getattr(device, "handle", device))
        self.window = getattr(window, "raw", getattr(window, "handle", window))
        self.descriptor = descriptor or SurfaceDescriptor()
        if self.descriptor.image_count < 1:
            raise ValueError("surface image_count must be at least 1")

        self.present_mode = self._supported_present_mode(self.descriptor.present_mode)
        self.current_image: SurfaceImage | None = None
        self.frame_number = 0

        check(
            sdl.SDL_SetGPUSwapchainParameters(
                self.device,
                self.window,
                to_sdl(self.descriptor.composition),
                to_sdl(self.present_mode),
            ),
            "SDL_SetGPUSwapchainParameters",
        )
        self.texture_format = from_sdl(
            TextureFormat,
            sdl.SDL_GetGPUSwapchainTextureFormat(self.device, self.window),
        )

    def acquire(self, command_buffer: Any) -> SurfaceImage | None:
        swapchain_texture = sdl.LP_SDL_GPUTexture()
        width = ctypes.c_uint32()
        height = ctypes.c_uint32()

        if not sdl.SDL_WaitAndAcquireGPUSwapchainTexture(
            command_buffer,
            self.window,
            ctypes.byref(swapchain_texture),
            ctypes.byref(width),
            ctypes.byref(height),
        ):
            raise SdlError(
                f"SDL_WaitAndAcquireGPUSwapchainTexture: {error_message()}"
            )

        if not swapchain_texture:
            self.current_image = None
            return None

        image = SurfaceImage(
            texture=swapchain_texture,
            width=int(width.value),
            height=int(height.value),
            format=self.texture_format,
            slot=self.frame_number % self.descriptor.image_count,
            frame_number=self.frame_number,
        )
        self.current_image = image
        self.frame_number += 1
        return image

    def clear_current_image(self) -> None:
        self.current_image = None

    def begin_render_pass(
        self,
        command_buffer: Any,
        clear_color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
        load_op: LoadOp | int = LoadOp.CLEAR,
        store_op: StoreOp | int = StoreOp.STORE,
    ):
        if self.current_image is None:
            raise RuntimeError("surface has no active image")

        color_target = sdl.SDL_GPUColorTargetInfo()
        color_target.texture = self.current_image.texture
        color_target.clear_color = sdl.SDL_FColor(*clear_color)
        color_target.load_op = to_sdl(load_op)
        color_target.store_op = to_sdl(store_op)

        return check(
            sdl.SDL_BeginGPURenderPass(
                command_buffer,
                ctypes.byref(color_target),
                1,
                None,
            ),
            "SDL_BeginGPURenderPass",
        )

    def _supported_present_mode(self, requested_mode: PresentMode | int) -> PresentMode | int:
        if sdl.SDL_WindowSupportsGPUPresentMode(
            self.device,
            self.window,
            to_sdl(requested_mode),
        ):
            return requested_mode
        return PresentMode.VSYNC
