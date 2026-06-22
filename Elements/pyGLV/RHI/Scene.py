from __future__ import annotations

from Elements.pyECSS.ECSSManager import ECSSManager
from Elements.pyGLV.RHI.Viewer import RHIWindow


class Scene:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("Creating RHI Scene Singleton Object")
            cls._instance = super(Scene, cls).__new__(cls)
            cls._renderWindow = None
            cls._gContext = None
            cls._world = ECSSManager()
        return cls._instance

    @property
    def renderWindow(self):
        return self._renderWindow

    @property
    def gContext(self):
        return self._gContext

    @property
    def world(self):
        return self._world

    def init(
        self,
        windowWidth=None,
        windowHeight=None,
        windowTitle=None,
        clear_color=(0.08, 0.09, 0.11, 1.0),
        depth_enabled=True,
    ):
        self._renderWindow = RHIWindow(
            windowWidth=windowWidth,
            windowHeight=windowHeight,
            windowTitle=windowTitle,
            scene=self,
            clear_color=clear_color,
            depth_enabled=depth_enabled,
        )
        self._gContext = self._renderWindow
        self._gContext.init()
        self._gContext.init_post()

    def render(self):
        still_running = self._gContext.event_input_process()
        self._gContext.display()
        return still_running

    def render_post(self):
        self._gContext.display_post()

    def shutdown(self):
        self._gContext.shutdown()
