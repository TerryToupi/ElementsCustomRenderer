import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import RenderMesh
from Elements.pyGLV.RHI import Key, QuitEvent, WindowCloseEvent
from Elements.pyGLV.RHI.Scene import Scene
from Elements.pyGLV.RHI.Components import (
    BuiltInMaterial,
    InitRHISystem,
    Material,
    RHIMesh,
    RenderRHISystem,
)
example_description = \
"This is a scene with some simple geometry, i.e., a colored cube. \n\
The cube is rendered via the simplest vertex and fragment shader. \n\
You cannot move the camera through the GUI. Hit ESC OR Close the window to quit." 

winWidth = 1024
winHeight = 768

scene = Scene()    

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))

entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)

node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))


axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))


#Simple Cube
vertexCube = np.array([
    [-0.5, -0.5, 0.5, 1.0],
    [-0.5, 0.5, 0.5, 1.0],
    [0.5, 0.5, 0.5, 1.0],
    [0.5, -0.5, 0.5, 1.0], 
    [-0.5, -0.5, -0.5, 1.0], 
    [-0.5, 0.5, -0.5, 1.0], 
    [0.5, 0.5, -0.5, 1.0], 
    [0.5, -0.5, -0.5, 1.0]
],dtype=np.float32) 
colorCube = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [0.0, 1.0, 1.0, 1.0]
], dtype=np.float32)

#index arrays for above vertex Arrays

indexCube = np.array((1,0,3, 1,3,2, 
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32) #rhombus out of two triangles




## ADD CUBE ##
# attach a simple cube in a RenderMesh so that RHIMesh can pick it up
mesh4.vertex_attributes.append(vertexCube)
mesh4.vertex_attributes.append(colorCube)
mesh4.vertex_index.append(indexCube)
vArray4 = scene.world.addComponent(node4, RHIMesh())
# decorated components and systems with sample, default pass-through shader with uniform MVP



model = util.translate(0.0,0.0,0.5)@util.scale(3)
eye = util.vec(1.0, 1.0, 1.0)
target = util.vec(0,0.0,0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)

# projMat = util.perspective(120.0, 1.33, 0.1, 100.0)
projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -10, 10.0)

mvpMat =  projMat @ view @ model


shaderDec4 = scene.world.addComponent(node4, Material(BuiltInMaterial.COLOR))
shaderDec4.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)



# Systems
initUpdate = scene.world.createSystem(InitRHISystem())
renderUpdate = scene.world.createSystem(RenderRHISystem())


scene.world.print()


running = True
# MAIN RENDERING LOOP
scene.init(windowWidth = winWidth, windowHeight = winHeight, windowTitle = "A Cube Scene via ECSS")

# pre-pass scenegraph to initialise RHI GPU buffers and pipelines
# needs an active RHI device and surface
scene.world.traverse_visit(initUpdate, scene.world.root)

while running:
    # Poll RHI events before recording GPU work for this frame.
    scene.renderWindow.begin_frame()
    for event in scene.renderWindow.poll_events():
        if isinstance(event, (QuitEvent, WindowCloseEvent)):
            running = False
    if scene.renderWindow.input.was_key_pressed(Key.ESCAPE):
        running = False
    if not running:
        break
    # display() acquires the swapchain texture and starts the render pass.
    scene.renderWindow.display()
    # RenderRHISystem records draw commands for each RHIMesh in the scene.
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()
    scene.renderWindow.end_frame()
    
scene.shutdown()
