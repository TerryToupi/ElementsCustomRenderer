from __future__ import annotations

from typing import Any

import numpy as np
from ._sdl import sdl

import Elements.pyECSS.System

from .Device import Device, GpuRenderPassDesc
from .Enums import TextureFormat, TextureUsage
from .ResourceManager import ResourceManager
from .Resources.Texture import TextureDescriptor
from .Surface import Surface, SurfaceDescriptor
from .Window import Window


class RHIWindow:
    def __init__(
        self,
        windowWidth: int | None = None,
        windowHeight: int | None = None,
        windowTitle: str | None = None,
        scene=None,
        eventManager=None,
        clear_color: tuple[float, float, float, float] = (0.08, 0.09, 0.11, 1.0),
        depth_enabled: bool = True,
        depth_format: TextureFormat | int = TextureFormat.D32_FLOAT,
    ):
        self._windowWidth = windowWidth or 1024
        self._windowHeight = windowHeight or 768
        self._windowTitle = windowTitle or "Elements RHI"
        self._scene = scene
        self._eventManager = eventManager or (
            scene.world.eventManager if scene is not None else None
        )

        self._window: Window | None = None
        self._device: Device | None = None
        self._surface: Surface | None = None
        self._resource_manager: ResourceManager | None = None
        self._command_buffer = None
        self._depth_texture_handle = None
        self._clear_color = clear_color
        self._depth_enabled = depth_enabled
        self._depth_format = depth_format
        self._wireframeMode = False
        self._myCamera = np.identity(4, dtype=np.float32)
        self._last_events = []

    @property
    def raw(self):
        return self.window.raw

    @property
    def window(self) -> Window:
        if self._window is None:
            raise RuntimeError("RHIWindow is not initialized")
        return self._window

    @property
    def device(self) -> Device:
        if self._device is None:
            raise RuntimeError("RHIWindow is not initialized")
        return self._device

    @property
    def surface(self) -> Surface:
        if self._surface is None:
            raise RuntimeError("RHIWindow is not initialized")
        return self._surface

    @property
    def resource_manager(self) -> ResourceManager:
        if self._resource_manager is None:
            raise RuntimeError("RHIWindow is not initialized")
        return self._resource_manager

    @property
    def command_buffer(self):
        if self._command_buffer is None:
            raise RuntimeError("RHI frame has not begun")
        return self._command_buffer

    @property
    def depth_enabled(self) -> bool:
        return self._depth_enabled

    @property
    def depth_format(self) -> TextureFormat | int:
        return self._depth_format

    @property
    def depth_texture(self):
        if self._depth_texture_handle is None:
            return None
        return self.resource_manager.get_texture(self._depth_texture_handle)

    @property
    def wireframe_mode(self) -> bool:
        return self._wireframeMode

    @wireframe_mode.setter
    def wireframe_mode(self, value: bool) -> None:
        self._wireframeMode = bool(value)

    @property
    def eventManager(self):
        return self._eventManager

    @eventManager.setter
    def eventManager(self, value):
        self._eventManager = value

    @property
    def scene(self):
        return self._scene

    @scene.setter
    def scene(self, value):
        self._scene = value

    @property
    def last_events(self) -> list[Any]:
        return self._last_events

    def init(self) -> None:
        self._window = Window(
            title=self._windowTitle,
            width=self._windowWidth,
            height=self._windowHeight,
        )
        self._device = Device()
        self._device.claim_window(self._window)
        self._surface = Surface(
            self._device,
            self._window,
            SurfaceDescriptor(),
        )
        self._resource_manager = ResourceManager(self._device)
        if self._depth_enabled:
            self._create_depth_texture(self._windowWidth, self._windowHeight)

    def init_post(self) -> None:
        pass

    def display(self) -> None:
        if self._command_buffer is not None:
            return
        command_buffer = self.device.acquire_command_buffer()
        command_buffer.acquire_surface_image(self.surface)
        command_buffer.begin_render_pass(
            GpuRenderPassDesc(
                surface=self.surface,
                clear_color=self._clear_color,
                depth_texture=self.depth_texture,
            )
        )
        self._command_buffer = command_buffer

    def display_post(self) -> None:
        if self._command_buffer is None:
            return
        command_buffer = self._command_buffer
        self._command_buffer = None
        try:
            command_buffer.end_render_pass()
            self.device.submit_command_buffer(command_buffer)
        finally:
            self.surface.clear_current_image()

    def event_input_process(self, running: bool = True) -> bool:
        events = self.window.poll_events()
        self._last_events = events
        running = running and not self.window.should_close

        for event in events:
            if self._is_resize_event(event):
                self._windowWidth = int(getattr(event.window, "data1", self._windowWidth))
                self._windowHeight = int(getattr(event.window, "data2", self._windowHeight))
                if self._depth_enabled:
                    self._create_depth_texture(self._windowWidth, self._windowHeight)
            elif self._is_wireframe_toggle(event):
                self._wireframeMode = not self._wireframeMode

        return running and not self.window.should_close

    def shutdown(self) -> None:
        if self._resource_manager is not None:
            self._resource_manager.close()
            self._resource_manager = None
        if self._device is not None and self._window is not None:
            self._device.release_window(self._window)
        if self._device is not None:
            self._device.close()
            self._device = None
        if self._window is not None:
            self._window.close()
            self._window = None

    def accept(self, system: Elements.pyECSS.System, event=None):
        if hasattr(system, "apply2RHIWindow"):
            system.apply2RHIWindow(self, event)

    def _create_depth_texture(self, width: int, height: int) -> None:
        if self._depth_texture_handle is not None:
            self.resource_manager.destroy_texture(self._depth_texture_handle)
        self._depth_texture_handle = self.resource_manager.create_texture(
            TextureDescriptor(
                width=max(1, int(width)),
                height=max(1, int(height)),
                format=self._depth_format,
                usage=TextureUsage.DEPTH_STENCIL_TARGET,
            )
        )

    @staticmethod
    def _is_resize_event(event: Any) -> bool:
        return event.type in {
            getattr(sdl, "SDL_EVENT_WINDOW_RESIZED", object()),
            getattr(sdl, "SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED", object()),
        }

    @staticmethod
    def _is_wireframe_toggle(event: Any) -> bool:
        if event.type != getattr(sdl, "SDL_EVENT_KEY_DOWN", None):
            return False
        key = getattr(event.key, "key", None)
        return key in {
            getattr(sdl, "SDLK_f", None),
            getattr(sdl, "SDLK_F", None),
        }
