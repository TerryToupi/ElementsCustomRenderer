from __future__ import annotations

import ctypes

import sdl3 as sdl

from Enums import WindowFlag, to_sdl
from Utils.Sdl import check, to_bytes


DEFAULT_WINDOW_FLAGS = WindowFlag.RESIZABLE | WindowFlag.HIGH_PIXEL_DENSITY


class Window:
    def __init__(
        self,
        title: str | bytes = "PySDL3 Window",
        width: int = 640,
        height: int = 480,
        flags: WindowFlag | int = DEFAULT_WINDOW_FLAGS,
        initialize_sdl: bool = True,
    ):
        self.handle = None
        self.should_close = False
        self._owns_video_subsystem = False

        if initialize_sdl and not sdl.SDL_WasInit(sdl.SDL_INIT_VIDEO):
            check(sdl.SDL_InitSubSystem(sdl.SDL_INIT_VIDEO), "SDL_InitSubSystem")
            self._owns_video_subsystem = True

        self.handle = check(
            sdl.SDL_CreateWindow(
                to_bytes(title),
                width,
                height,
                to_sdl(flags),
            ),
            "SDL_CreateWindow",
        )

    @property
    def raw(self):
        if self.handle is None:
            raise RuntimeError("window is closed")
        return self.handle

    @staticmethod
    def event_wants_close(event) -> bool:
        if event.type == sdl.SDL_EVENT_QUIT:
            return True
        if event.type == sdl.SDL_EVENT_WINDOW_CLOSE_REQUESTED:
            return True
        if event.type == sdl.SDL_EVENT_KEY_DOWN and event.key.key == sdl.SDLK_ESCAPE:
            return True
        return False

    def poll_events(self) -> list[sdl.SDL_Event]:
        events: list[sdl.SDL_Event] = []
        event = sdl.SDL_Event()

        while sdl.SDL_PollEvent(ctypes.byref(event)):
            copied_event = sdl.SDL_Event.from_buffer_copy(event)
            if self.event_wants_close(copied_event):
                self.should_close = True
            events.append(copied_event)

        return events

    def poll(self) -> bool:
        self.poll_events()
        return not self.should_close

    def close(self) -> None:
        if self.handle is not None:
            sdl.SDL_DestroyWindow(self.handle)
            self.handle = None

        if self._owns_video_subsystem:
            sdl.SDL_QuitSubSystem(sdl.SDL_INIT_VIDEO)
            self._owns_video_subsystem = False

    def __enter__(self) -> "Window":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
