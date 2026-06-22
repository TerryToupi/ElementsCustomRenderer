"""Basic RHI input and event handling."""

from Elements.pyGLV.RHI import (
    Key,
    MouseButton,
    MouseButtonDownEvent,
    QuitEvent,
    RHIWindow,
    WindowCloseEvent,
    WindowResizeEvent,
)


window = RHIWindow(windowTitle="Elements RHI input events. Hit ESC or close the window.")
window.init()

running = True
try:
    while running:
        window.begin_frame()

        for event in window.poll_events():
            if isinstance(event, (QuitEvent, WindowCloseEvent)):
                running = False
            elif isinstance(event, WindowResizeEvent):
                print(f"resized to {event.width}x{event.height}")
            elif isinstance(event, MouseButtonDownEvent):
                print(f"{event.button.value} click at {event.x:.0f}, {event.y:.0f}")

        if window.input.is_key_down(Key.W):
            print("move forward")
        if window.input.was_key_pressed(Key.ESCAPE):
            running = False
        if window.input.was_mouse_button_pressed(MouseButton.LEFT):
            print("left mouse pressed")

        window.display()
        window.display_post()
        window.end_frame()
finally:
    window.shutdown()
