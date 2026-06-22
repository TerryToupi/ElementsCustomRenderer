"""Running a basic empty RHI window."""

from Elements.pyGLV.RHI import Key, QuitEvent, RHIWindow, WindowCloseEvent

    
gWindow = RHIWindow(windowTitle="A simple empty RHI window. Hit ESC or close the window to quit!")
gWindow.init()



running = True
while running:
    # RHI frame lifecycle: reset input, poll window events, render, submit.
    gWindow.begin_frame()
    for event in gWindow.poll_events():
        if isinstance(event, (QuitEvent, WindowCloseEvent)):
            running = False
    if gWindow.input.was_key_pressed(Key.ESCAPE):
        running = False
    if not running:
        break
    # display() begins a simple render pass; display_post() submits it.
    gWindow.display()
    gWindow.display_post()
    gWindow.end_frame()
gWindow.shutdown()
