"""Running a basic empty RHI window."""

from Elements.pyGLV.RHI.Viewer import RHIWindow

    
gWindow = RHIWindow(windowTitle="A simple empty RHI window. Hit ESC or close the window to quit!")
gWindow.init()



running = True
while running:
  running = gWindow.event_input_process()
  gWindow.display()
  gWindow.display_post()
gWindow.shutdown()
