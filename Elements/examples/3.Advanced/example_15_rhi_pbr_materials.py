import math
import time

import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.RHI import Key, QuitEvent, WindowCloseEvent
from Elements.pyGLV.RHI.Components import (
    BuiltInMaterial,
    InitRHISystem,
    Material,
    RHIMesh,
    RenderRHISystem,
)
from Elements.pyGLV.RHI.Enums import PrimitiveType
from Elements.pyGLV.RHI.Scene import Scene


example_description = (
    "RHI PBR material example. Rows vary metallic, columns vary roughness. "
    "Press F to toggle wireframe, ESC or close the window to quit."
)

winWidth = 1280
winHeight = 800

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))


def create_uv_sphere(radius=0.55, stacks=32, sectors=32):
    vertices = []
    colors = []
    normals = []
    indices = []

    for stack in range(stacks + 1):
        stack_angle = math.pi / 2.0 - stack * math.pi / stacks
        xy = radius * math.cos(stack_angle)
        z = radius * math.sin(stack_angle)

        for sector in range(sectors + 1):
            sector_angle = sector * 2.0 * math.pi / sectors
            x = xy * math.cos(sector_angle)
            y = xy * math.sin(sector_angle)
            normal = util.normalise(util.vec(x, y, z))

            vertices.append([x, y, z, 1.0])
            colors.append([1.0, 1.0, 1.0, 1.0])
            normals.append([normal[0], normal[1], normal[2], 0.0])

    for stack in range(stacks):
        row = stack * (sectors + 1)
        next_row = row + sectors + 1

        for sector in range(sectors):
            if stack != 0:
                indices.extend([row + sector, next_row + sector, row + sector + 1])
            if stack != stacks - 1:
                indices.extend(
                    [row + sector + 1, next_row + sector, next_row + sector + 1]
                )

    return (
        np.array(vertices, dtype=np.float32),
        np.array(colors, dtype=np.float32),
        np.array(normals, dtype=np.float32),
        np.array(indices, dtype=np.uint32),
    )


def add_mesh_entity(
    name,
    transform,
    vertex_attributes,
    indices,
    material_kind,
    primitive=PrimitiveType.TRIANGLELIST,
):
    entity = scene.world.createEntity(Entity(name=name))
    scene.world.addEntityChild(rootEntity, entity)
    transform_component = scene.world.addComponent(
        entity, BasicTransform(name=f"{name}_TRS", trs=transform)
    )
    mesh = scene.world.addComponent(entity, RenderMesh(name=f"{name}_mesh"))
    for attribute in vertex_attributes:
        mesh.vertex_attributes.append(attribute)
    mesh.vertex_index.append(indices)
    scene.world.addComponent(entity, RHIMesh(primitive=primitive))
    material = scene.world.addComponent(entity, Material(material_kind))
    return transform_component, material


sphere_vertices, sphere_colors, sphere_normals, sphere_indices = create_uv_sphere()
spheres = []

roughness_values = [0.12, 0.28, 0.48, 0.68, 0.88]
metallic_values = [0.0, 0.5, 1.0]

for row, metallic in enumerate(metallic_values):
    for column, roughness in enumerate(roughness_values):
        x = (column - 2) * 1.55
        y = (1 - row) * 1.55
        transform, material = add_mesh_entity(
            f"PBR_m{metallic:.2f}_r{roughness:.2f}",
            util.translate(x, y, 0.0),
            (sphere_vertices, sphere_colors, sphere_normals),
            sphere_indices,
            BuiltInMaterial.PBR,
        )
        material.setUniformVariable("albedoColor", util.vec(0.95, 0.56, 0.28))
        material.setUniformVariable("metallic", metallic)
        material.setUniformVariable("roughness", roughness)
        material.setUniformVariable("ao", 1.0)
        material.setUniformVariable("ambientStr", 0.035)
        spheres.append((transform, material))


axis_vertices = np.array(
    [
        [-4.4, -3.0, 0.0, 1.0],
        [4.4, -3.0, 0.0, 1.0],
        [-4.4, 3.0, 0.0, 1.0],
        [-4.4, -3.0, 0.0, 1.0],
    ],
    dtype=np.float32,
)
axis_colors = np.array(
    [
        [0.95, 0.45, 0.12, 1.0],
        [0.95, 0.45, 0.12, 1.0],
        [0.25, 0.65, 0.95, 1.0],
        [0.25, 0.65, 0.95, 1.0],
    ],
    dtype=np.float32,
)
axis_indices = np.array([0, 1, 2, 3], dtype=np.uint32)
axis_transform, axis_material = add_mesh_entity(
    "material_axes",
    util.identity(),
    (axis_vertices, axis_colors),
    axis_indices,
    BuiltInMaterial.COLOR,
    PrimitiveType.LINELIST,
)

light_vertices, light_colors, light_normals, light_indices = create_uv_sphere(
    radius=0.16, stacks=12, sectors=12
)
light_transform, light_marker_material = add_mesh_entity(
    "moving_light_marker",
    util.identity(),
    (light_vertices, light_colors, light_normals),
    light_indices,
    BuiltInMaterial.PBR,
)
light_marker_material.setUniformVariable("albedoColor", util.vec(1.0, 0.92, 0.72))
light_marker_material.setUniformVariable("metallic", 0.0)
light_marker_material.setUniformVariable("roughness", 0.2)
light_marker_material.setUniformVariable("ao", 1.0)
light_marker_material.setUniformVariable("ambientStr", 0.7)


renderUpdate = scene.world.createSystem(RenderRHISystem())
initUpdate = scene.world.createSystem(InitRHISystem())

scene.init(
    windowWidth=winWidth,
    windowHeight=winHeight,
    windowTitle="Elements RHI: PBR Materials",
    clear_color=(0.025, 0.028, 0.035, 1.0),
)
scene.world.traverse_visit(initUpdate, scene.world.root)

eye = util.vec(0.0, 0.0, 8.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
projMat = util.perspective(45.0, winWidth / winHeight, 0.1, 100.0)

start_time = time.perf_counter()
running = True

while running:
    # Poll RHI events first; after this, input state is valid for this frame.
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

    # CPU-side animation: move the point light before uniforms are uploaded.
    elapsed = time.perf_counter() - start_time
    light_position = util.vec(
        3.8 * math.cos(elapsed * 0.7),
        2.8,
        3.8 * math.sin(elapsed * 0.7) + 2.5,
    )
    light_transform.trs = util.translate(
        light_position[0], light_position[1], light_position[2]
    )

    axis_material.setUniformVariable(
        "modelViewProj", projMat @ view @ axis_transform.trs
    )

    for transform, material in spheres:
        model = transform.trs
        material.setUniformVariable("modelViewProj", projMat @ view @ model)
        material.setUniformVariable("model", model)
        material.setUniformVariable("viewPos", eye)
        material.setUniformVariable("lightPos", light_position)
        material.setUniformVariable("lightColor", util.vec(1.0, 0.96, 0.88))
        material.setUniformVariable("lightIntensity", 48.0)

    light_model = light_transform.trs
    light_marker_material.setUniformVariable(
        "modelViewProj", projMat @ view @ light_model
    )
    light_marker_material.setUniformVariable("model", light_model)
    light_marker_material.setUniformVariable("viewPos", eye)
    light_marker_material.setUniformVariable("lightPos", light_position)
    light_marker_material.setUniformVariable("lightColor", util.vec(1.0, 0.96, 0.88))
    light_marker_material.setUniformVariable("lightIntensity", 16.0)

    # RenderRHISystem reads RHIMesh + Material components and records draw calls.
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()
    scene.renderWindow.end_frame()

scene.shutdown()
