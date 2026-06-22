"""
Running the basic RenderWindow with the concrete basic Compoment of the decorator
pattern, that is the RHIWindow, without any decorator on top.
"""

from Elements.pyGLV.RHI.Viewer import RHIWindow

gWindow = RHIWindow(windowTitle="A simple empty RHI window. Hit ESC or close the window to quit!")
gWindow.init()



running = True
# MAIN RENDERING LOOP

while running:
    running = gWindow.event_input_process()
    gWindow.display()
    gWindow.display_post()
gWindow.shutdown()
