import math
import time

import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.RHI._sdl import sdl
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
    "RHI PBR camera-control example. Right mouse drag or arrow keys orbit, "
    "WASD pans, Q/E or the mouse wheel zooms. Press F for wireframe."
)

winWidth = 1280
winHeight = 800

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))


class OrbitCameraController:
    def __init__(self, target=(0.0, 0.0, 0.0), distance=8.0):
        self.target = np.array(target, dtype=np.float32)
        self.distance = float(distance)
        self.yaw = -35.0
        self.pitch = 18.0
        self.orbiting = False
        self.panning = False
        self.held_keys = set()

    def update(self, events, dt):
        for event in events:
            event_type = getattr(event, "type", None)
            if event_type == getattr(sdl, "SDL_EVENT_KEY_DOWN", None):
                self.held_keys.add(getattr(event.key, "key", None))
            elif event_type == getattr(sdl, "SDL_EVENT_KEY_UP", None):
                self.held_keys.discard(getattr(event.key, "key", None))
            elif event_type == getattr(sdl, "SDL_EVENT_MOUSE_BUTTON_DOWN", None):
                button = getattr(event.button, "button", None)
                self.orbiting = button == getattr(sdl, "SDL_BUTTON_RIGHT", 3)
                self.panning = button == getattr(sdl, "SDL_BUTTON_MIDDLE", 2)
            elif event_type == getattr(sdl, "SDL_EVENT_MOUSE_BUTTON_UP", None):
                button = getattr(event.button, "button", None)
                if button == getattr(sdl, "SDL_BUTTON_RIGHT", 3):
                    self.orbiting = False
                elif button == getattr(sdl, "SDL_BUTTON_MIDDLE", 2):
                    self.panning = False
            elif event_type == getattr(sdl, "SDL_EVENT_MOUSE_MOTION", None):
                dx = float(getattr(event.motion, "xrel", 0.0))
                dy = float(getattr(event.motion, "yrel", 0.0))
                if self.orbiting:
                    self.yaw -= dx * 0.25
                    self.pitch -= dy * 0.25
                elif self.panning:
                    self._pan(-dx * 0.005 * self.distance, dy * 0.005 * self.distance)
            elif event_type == getattr(sdl, "SDL_EVENT_MOUSE_WHEEL", None):
                wheel_y = float(getattr(event.wheel, "y", 0.0))
                self.distance *= pow(0.88, wheel_y)

        self.yaw += self._axis("right", "left") * 70.0 * dt
        self.pitch += self._axis("up", "down") * 70.0 * dt
        self.distance *= pow(0.35, self._axis("zoom_in", "zoom_out") * dt)
        self._pan(
            self._axis("pan_right", "pan_left") * 2.8 * dt,
            self._axis("pan_up", "pan_down") * 2.8 * dt,
        )

        self.pitch = float(np.clip(self.pitch, -80.0, 80.0))
        self.distance = float(np.clip(self.distance, 2.4, 20.0))

    def view_matrix(self):
        eye = self.eye_position()
        return util.lookat(eye, self.target, util.vec(0.0, 1.0, 0.0))

    def eye_position(self):
        yaw = math.radians(self.yaw)
        pitch = math.radians(self.pitch)
        direction = np.array(
            [
                math.cos(pitch) * math.sin(yaw),
                math.sin(pitch),
                math.cos(pitch) * math.cos(yaw),
            ],
            dtype=np.float32,
        )
        return self.target + direction * self.distance

    def _pan(self, right_delta, up_delta):
        if right_delta == 0.0 and up_delta == 0.0:
            return

        eye = self.eye_position()
        forward = util.normalise(self.target - eye)
        right = util.normalise(np.cross(forward, util.vec(0.0, 1.0, 0.0)))
        up = util.normalise(np.cross(right, forward))
        self.target += right * right_delta + up * up_delta

    def _axis(self, positive, negative):
        return float(self._any_key(KEY_GROUPS[positive])) - float(
            self._any_key(KEY_GROUPS[negative])
        )

    def _any_key(self, keys):
        return any(key in self.held_keys for key in keys)


def key_codes(lowercase):
    uppercase = lowercase.upper()
    codes = {
        ord(lowercase),
        ord(uppercase),
        getattr(sdl, f"SDLK_{lowercase}", ord(lowercase)),
        getattr(sdl, f"SDLK_{uppercase}", ord(uppercase)),
    }
    return {code for code in codes if code is not None}


KEY_GROUPS = {
    "left": key_codes("j") | {getattr(sdl, "SDLK_LEFT", None)},
    "right": key_codes("l") | {getattr(sdl, "SDLK_RIGHT", None)},
    "up": key_codes("i") | {getattr(sdl, "SDLK_UP", None)},
    "down": key_codes("k") | {getattr(sdl, "SDLK_DOWN", None)},
    "pan_left": key_codes("a"),
    "pan_right": key_codes("d"),
    "pan_up": key_codes("w"),
    "pan_down": key_codes("s"),
    "zoom_in": key_codes("q"),
    "zoom_out": key_codes("e"),
}
KEY_GROUPS = {
    name: {key for key in keys if key is not None} for name, keys in KEY_GROUPS.items()
}


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


def create_grid(size=6, step=1.0):
    vertices = []
    colors = []
    indices = []
    line_index = 0

    for i in range(-size, size + 1):
        color = [0.18, 0.22, 0.26, 1.0]
        if i == 0:
            color = [0.38, 0.44, 0.50, 1.0]

        vertices.extend(
            [
                [i * step, 0.0, -size * step, 1.0],
                [i * step, 0.0, size * step, 1.0],
                [-size * step, 0.0, i * step, 1.0],
                [size * step, 0.0, i * step, 1.0],
            ]
        )
        colors.extend([color, color, color, color])
        indices.extend([line_index, line_index + 1, line_index + 2, line_index + 3])
        line_index += 4

    return (
        np.array(vertices, dtype=np.float32),
        np.array(colors, dtype=np.float32),
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
pbr_objects = []

materials = [
    ("brushed_copper", util.vec(0.95, 0.56, 0.28), 1.0, 0.32),
    ("matte_ceramic", util.vec(0.55, 0.72, 0.84), 0.0, 0.78),
    ("polished_coal", util.vec(0.08, 0.09, 0.10), 0.0, 0.18),
    ("soft_gold", util.vec(1.0, 0.78, 0.34), 1.0, 0.52),
]

positions = [(-2.1, 0.65, -1.1), (0.0, 0.65, 0.0), (2.1, 0.65, -1.1), (0.0, 1.7, 1.35)]
for (name, albedo, metallic, roughness), position in zip(materials, positions):
    transform, material = add_mesh_entity(
        name,
        util.translate(position[0], position[1], position[2]),
        (sphere_vertices, sphere_colors, sphere_normals),
        sphere_indices,
        BuiltInMaterial.PBR,
    )
    material.setUniformVariable("albedoColor", albedo)
    material.setUniformVariable("metallic", metallic)
    material.setUniformVariable("roughness", roughness)
    material.setUniformVariable("ao", 1.0)
    material.setUniformVariable("ambientStr", 0.04)
    pbr_objects.append((transform, material))


grid_vertices, grid_colors, grid_indices = create_grid(size=7, step=0.75)
grid_transform, grid_material = add_mesh_entity(
    "camera_reference_grid",
    util.identity(),
    (grid_vertices, grid_colors),
    grid_indices,
    BuiltInMaterial.COLOR,
    PrimitiveType.LINELIST,
)

light_vertices, light_colors, light_normals, light_indices = create_uv_sphere(
    radius=0.14, stacks=12, sectors=12
)
light_transform, light_material = add_mesh_entity(
    "moving_light",
    util.identity(),
    (light_vertices, light_colors, light_normals),
    light_indices,
    BuiltInMaterial.PBR,
)
light_material.setUniformVariable("albedoColor", util.vec(1.0, 0.92, 0.70))
light_material.setUniformVariable("metallic", 0.0)
light_material.setUniformVariable("roughness", 0.25)
light_material.setUniformVariable("ao", 1.0)
light_material.setUniformVariable("ambientStr", 0.8)
pbr_objects.append((light_transform, light_material))


renderUpdate = scene.world.createSystem(RenderRHISystem())
initUpdate = scene.world.createSystem(InitRHISystem())

scene.init(
    windowWidth=winWidth,
    windowHeight=winHeight,
    windowTitle="Elements RHI: PBR Camera Control",
    clear_color=(0.025, 0.028, 0.035, 1.0),
)
scene.world.traverse_visit(initUpdate, scene.world.root)

camera = OrbitCameraController(target=(0.0, 0.8, 0.0), distance=7.4)
start_time = time.perf_counter()
last_time = start_time
running = True

while running:
    running = scene.render()

    now = time.perf_counter()
    dt = min(now - last_time, 1.0 / 20.0)
    last_time = now

    camera.update(scene.renderWindow.last_events, dt)
    view = camera.view_matrix()
    eye = camera.eye_position()
    aspect = max(1, scene.renderWindow._windowWidth) / max(
        1, scene.renderWindow._windowHeight
    )
    projMat = util.perspective(45.0, aspect, 0.1, 100.0)

    elapsed = now - start_time
    light_position = util.vec(
        3.4 * math.cos(elapsed * 0.8),
        3.0 + 0.55 * math.sin(elapsed * 1.3),
        3.4 * math.sin(elapsed * 0.8),
    )
    light_transform.trs = util.translate(
        light_position[0], light_position[1], light_position[2]
    )

    grid_material.setUniformVariable(
        "modelViewProj", projMat @ view @ grid_transform.trs
    )

    for transform, material in pbr_objects:
        model = transform.trs
        material.setUniformVariable("modelViewProj", projMat @ view @ model)
        material.setUniformVariable("model", model)
        material.setUniformVariable("viewPos", eye)
        material.setUniformVariable("lightPos", light_position)
        material.setUniformVariable("lightColor", util.vec(1.0, 0.96, 0.88))
        material.setUniformVariable("lightIntensity", 52.0)

    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()
