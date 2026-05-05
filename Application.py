from __future__ import annotations

import argparse
import ctypes
from dataclasses import dataclass
from pathlib import Path

import sdl3 as sdl

from Device import Device
from ResourceManager import (
    GraphicsPipelineHandle,
    ResourceManager,
    ShaderHandle,
)
from Resources import (
    GraphicsPipelineDescriptor,
    ShaderDescriptor,
)
from Utils.Sdl import SdlError, check, error_message
from Window import Window


SHADER_DIR = Path(__file__).resolve().with_name("Shaders")
TRIANGLE_VERTEX_SHADER = SHADER_DIR / "triangle.vert.spv.b64"
TRIANGLE_FRAGMENT_SHADER = SHADER_DIR / "triangle.frag.spv.b64"


@dataclass(slots=True)
class ApplicationConfig:
    title: str = "PySDL3 Triangle"
    width: int = 640
    height: int = 480
    max_frames: int = 0
    frame_delay_ms: int = 16
    debug_gpu: bool = True


@dataclass(slots=True)
class TriangleResources:
    vertex_shader: ShaderHandle | None = None
    fragment_shader: ShaderHandle | None = None
    pipeline: GraphicsPipelineHandle | None = None


class Application:
    def __init__(self, config: ApplicationConfig | None = None):
        self.config = config or ApplicationConfig()
        self.window: Window | None = None
        self.device: Device | None = None
        self.resources: ResourceManager | None = None
        self.triangle_resources = TriangleResources()
        self.frame_count = 0
        self._window_claimed = False

    @property
    def initialized(self) -> bool:
        return (
            self.window is not None
            and self.device is not None
            and self.resources is not None
        )

    def initialize(self) -> None:
        if self.initialized:
            return

        self.window = Window(
            self.config.title,
            self.config.width,
            self.config.height,
        )
        self.device = Device(debug_mode=self.config.debug_gpu)
        self.device.claim_window(self.window)
        self._window_claimed = True
        self.resources = ResourceManager(self.device)
        self._create_triangle_resources()

    def run(self) -> int:
        self.initialize()
        self.frame_count = 0

        try:
            while self._running():
                self.update()
                if not self._running():
                    break

                self.render()
                self.frame_count += 1

                if (
                    self.config.max_frames > 0
                    and self.frame_count >= self.config.max_frames
                ):
                    break

                if self.config.frame_delay_ms > 0:
                    sdl.SDL_Delay(self.config.frame_delay_ms)
        finally:
            self.shutdown()

        return self.frame_count

    def update(self) -> None:
        if self.window is None:
            return

        self.window.poll_events()

    def render(self) -> None:
        if (
            self.device is None
            or self.window is None
            or self.resources is None
            or self.triangle_resources.pipeline is None
        ):
            return

        command_buffer = check(
            sdl.SDL_AcquireGPUCommandBuffer(self.device.raw),
            "SDL_AcquireGPUCommandBuffer",
        )

        swapchain_texture = sdl.LP_SDL_GPUTexture()
        width = ctypes.c_uint32()
        height = ctypes.c_uint32()

        if not sdl.SDL_WaitAndAcquireGPUSwapchainTexture(
            command_buffer,
            self.window.raw,
            ctypes.byref(swapchain_texture),
            ctypes.byref(width),
            ctypes.byref(height),
        ):
            sdl.SDL_CancelGPUCommandBuffer(command_buffer)
            raise SdlError(
                f"SDL_WaitAndAcquireGPUSwapchainTexture: {error_message()}"
            )

        if swapchain_texture:
            color_target = sdl.SDL_GPUColorTargetInfo()
            color_target.texture = swapchain_texture
            color_target.clear_color = sdl.SDL_FColor(0.02, 0.02, 0.04, 1.0)
            color_target.load_op = sdl.SDL_GPU_LOADOP_CLEAR
            color_target.store_op = sdl.SDL_GPU_STOREOP_STORE

            render_pass = check(
                sdl.SDL_BeginGPURenderPass(
                    command_buffer,
                    ctypes.byref(color_target),
                    1,
                    None,
                ),
                "SDL_BeginGPURenderPass",
            )
            pipeline = self.resources.get_graphics_pipeline(
                self.triangle_resources.pipeline
            )
            sdl.SDL_BindGPUGraphicsPipeline(render_pass, pipeline.handle)
            sdl.SDL_DrawGPUPrimitives(render_pass, 3, 1, 0, 0)
            sdl.SDL_EndGPURenderPass(render_pass)

        check(
            sdl.SDL_SubmitGPUCommandBuffer(command_buffer),
            "SDL_SubmitGPUCommandBuffer",
        )

    def shutdown(self) -> None:
        if self.resources is not None:
            self.resources.close()
            self.resources = None
            self.triangle_resources = TriangleResources()

        if self._window_claimed and self.device is not None and self.window is not None:
            self.device.release_window(self.window)
            self._window_claimed = False

        if self.device is not None:
            self.device.close()
            self.device = None

        if self.window is not None:
            self.window.close()
            self.window = None

    def _create_triangle_resources(self) -> None:
        if self.resources is None or self.window is None:
            raise RuntimeError("resource manager is not initialized")

        vertex_shader = self.resources.create_shader(
            self._load_shader(
                TRIANGLE_VERTEX_SHADER,
                sdl.SDL_GPU_SHADERSTAGE_VERTEX,
            )
        )
        fragment_shader = self.resources.create_shader(
            self._load_shader(
                TRIANGLE_FRAGMENT_SHADER,
                sdl.SDL_GPU_SHADERSTAGE_FRAGMENT,
            )
        )
        pipeline = self.resources.create_graphics_pipeline(
            GraphicsPipelineDescriptor(
                vertex_shader=vertex_shader,
                fragment_shader=fragment_shader,
                color_target_formats=(
                    self.resources.get_swapchain_texture_format(self.window),
                ),
            )
        )

        self.triangle_resources = TriangleResources(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader,
            pipeline=pipeline,
        )

    @staticmethod
    def _load_shader(path: Path, stage: int) -> ShaderDescriptor:
        return ShaderDescriptor.from_base64(path.read_text(encoding="ascii"), stage)

    def _running(self) -> bool:
        if self.window is None:
            return False
        return not self.window.should_close

    def __enter__(self) -> "Application":
        self.initialize()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.shutdown()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a dummy PySDL3 application.")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument(
        "--frames",
        type=int,
        default=0,
        help="Exit after this many frames; 0 runs until the window is closed.",
    )
    parser.add_argument(
        "--frame-delay-ms",
        type=int,
        default=16,
        help="Delay between frames in milliseconds.",
    )
    parser.add_argument(
        "--no-gpu-debug",
        action="store_true",
        help="Disable SDL GPU debug mode.",
    )
    args = parser.parse_args()

    config = ApplicationConfig(
        width=args.width,
        height=args.height,
        max_frames=args.frames,
        frame_delay_ms=args.frame_delay_ms,
        debug_gpu=not args.no_gpu_debug,
    )

    try:
        Application(config).run()
    except SdlError as exc:
        print(exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
