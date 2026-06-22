"""Basic RHI input and event handling.

Read this example before the graphics and compute pipeline examples.
It shows the frame lifecycle used by the RHI examples:

1. begin_frame() clears one-frame input state.
2. poll_events() converts SDL events into engine-level RHI events.
3. window.input answers questions such as "is W held?".
4. display() / display_post() submit one empty frame.
5. end_frame() closes the example frame lifecycle.
"""

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
        # Start a new frame. Pressed/released sets and mouse delta are reset here.
        window.begin_frame()

        # poll_events() returns RHI events, not raw SDL events.
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

        # This example has no geometry, but it still presents a clear frame.
        window.display()
        window.display_post()
        window.end_frame()
finally:
    # Always release GPU/window resources, even when the loop exits by exception.
    window.shutdown()
