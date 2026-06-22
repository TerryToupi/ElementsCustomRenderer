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
    "RHI meshlet imitation. A torus is partitioned into small triangle clusters; "
    "each cluster is submitted as an independent mesh with a local bound."
)

winWidth = 1280
winHeight = 800

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))


class OrbitCameraController:
    def __init__(self, target=(0.0, 0.0, 0.0), distance=7.0):
        self.target = np.array(target, dtype=np.float32)
        self.distance = float(distance)
        self.yaw = -30.0
        self.pitch = 24.0
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
                    self._pan(-dx * 0.004 * self.distance, dy * 0.004 * self.distance)
            elif event_type == getattr(sdl, "SDL_EVENT_MOUSE_WHEEL", None):
                wheel_y = float(getattr(event.wheel, "y", 0.0))
                self.distance *= pow(0.88, wheel_y)

        self.yaw += self._axis("right", "left") * 70.0 * dt
        self.pitch += self._axis("up", "down") * 70.0 * dt
        self.distance *= pow(0.35, self._axis("zoom_in", "zoom_out") * dt)
        self._pan(
            self._axis("pan_right", "pan_left") * 2.6 * dt,
            self._axis("pan_up", "pan_down") * 2.6 * dt,
        )

        self.pitch = float(np.clip(self.pitch, -80.0, 80.0))
        self.distance = float(np.clip(self.distance, 2.5, 18.0))

    def view_matrix(self):
        return util.lookat(self.eye_position(), self.target, util.vec(0.0, 1.0, 0.0))

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


def create_torus(major_radius=1.45, minor_radius=0.46, major_segments=56, minor_segments=18):
    vertices = []
    colors = []
    normals = []
    indices = []

    for major in range(major_segments):
        u = 2.0 * math.pi * major / major_segments
        ring_center = np.array(
            [major_radius * math.cos(u), 0.0, major_radius * math.sin(u)],
            dtype=np.float32,
        )

        for minor in range(minor_segments):
            v = 2.0 * math.pi * minor / minor_segments
            normal = np.array(
                [math.cos(u) * math.cos(v), math.sin(v), math.sin(u) * math.cos(v)],
                dtype=np.float32,
            )
            position = ring_center + normal * minor_radius
            vertices.append([position[0], position[1], position[2], 1.0])
            colors.append([1.0, 1.0, 1.0, 1.0])
            normals.append([normal[0], normal[1], normal[2], 0.0])

    for major in range(major_segments):
        next_major = (major + 1) % major_segments
        for minor in range(minor_segments):
            next_minor = (minor + 1) % minor_segments
            a = major * minor_segments + minor
            b = next_major * minor_segments + minor
            c = next_major * minor_segments + next_minor
            d = major * minor_segments + next_minor
            indices.extend([a, b, d, d, b, c])

    return (
        np.array(vertices, dtype=np.float32),
        np.array(colors, dtype=np.float32),
        np.array(normals, dtype=np.float32),
        np.array(indices, dtype=np.uint32),
    )


def make_palette(count):
    colors = []
    for index in range(count):
        hue = index / max(1, count)
        r, g, b = hsv_to_rgb(hue, 0.62, 0.98)
        colors.append([r, g, b, 1.0])
    return colors


def hsv_to_rgb(h, s, v):
    sector = int(h * 6.0)
    f = h * 6.0 - sector
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    sector %= 6
    if sector == 0:
        return v, t, p
    if sector == 1:
        return q, v, p
    if sector == 2:
        return p, v, t
    if sector == 3:
        return p, q, v
    if sector == 4:
        return t, p, v
    return v, p, q


def split_into_meshlets(vertices, normals, indices, max_triangles=28):
    triangles = indices.reshape((-1, 3))
    palette = make_palette(math.ceil(len(triangles) / max_triangles))
    meshlets = []
    global_center = np.mean(vertices[:, :3], axis=0)

    for meshlet_index, start in enumerate(range(0, len(triangles), max_triangles)):
        tri_slice = triangles[start : start + max_triangles]
        source_indices = []
        local_index_map = {}
        local_indices = []

        for source_index in tri_slice.reshape(-1):
            source_index = int(source_index)
            if source_index not in local_index_map:
                local_index_map[source_index] = len(source_indices)
                source_indices.append(source_index)
            local_indices.append(local_index_map[source_index])

        source_indices = np.array(source_indices, dtype=np.uint32)
        local_vertices = vertices[source_indices].copy()
        local_normals = normals[source_indices].copy()
        local_colors = np.array(
            [palette[meshlet_index]] * len(source_indices), dtype=np.float32
        )
        local_indices = np.array(local_indices, dtype=np.uint32)

        center = np.mean(local_vertices[:, :3], axis=0)
        radius = float(np.max(np.linalg.norm(local_vertices[:, :3] - center, axis=1)))
        explode_dir = center - global_center
        direction_length = np.linalg.norm(explode_dir)
        if direction_length > 0.0001:
            explode_dir = explode_dir / direction_length
        else:
            explode_dir = np.array([0.0, 1.0, 0.0], dtype=np.float32)

        meshlets.append(
            {
                "vertices": local_vertices,
                "colors": local_colors,
                "normals": local_normals,
                "indices": local_indices,
                "center": center.astype(np.float32),
                "radius": radius,
                "explode_dir": explode_dir.astype(np.float32),
                "color": palette[meshlet_index],
                "triangles": len(tri_slice),
                "vertices_count": len(source_indices),
            }
        )

    return meshlets


def create_bound_lines(center, radius, color, segments=28):
    vertices = []
    colors = []
    indices = []
    axes = ((0, 1), (0, 2), (1, 2))

    for plane_index, (a, b) in enumerate(axes):
        base_index = len(vertices)
        for segment in range(segments):
            angle = 2.0 * math.pi * segment / segments
            position = np.array(center, dtype=np.float32)
            position[a] += math.cos(angle) * radius
            position[b] += math.sin(angle) * radius
            vertices.append([position[0], position[1], position[2], 1.0])
            colors.append(color)

        for segment in range(segments):
            indices.extend(
                [
                    base_index + segment,
                    base_index + ((segment + 1) % segments),
                ]
            )

    return (
        np.array(vertices, dtype=np.float32),
        np.array(colors, dtype=np.float32),
        np.array(indices, dtype=np.uint32),
    )


def create_grid(size=6, step=0.75):
    vertices = []
    colors = []
    indices = []
    line_index = 0

    for i in range(-size, size + 1):
        color = [0.16, 0.19, 0.22, 1.0]
        if i == 0:
            color = [0.34, 0.40, 0.46, 1.0]

        vertices.extend(
            [
                [i * step, -1.05, -size * step, 1.0],
                [i * step, -1.05, size * step, 1.0],
                [-size * step, -1.05, i * step, 1.0],
                [size * step, -1.05, i * step, 1.0],
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


vertices, colors, normals, indices = create_torus()
meshlets = split_into_meshlets(vertices, normals, indices, max_triangles=28)
render_items = []

for index, meshlet in enumerate(meshlets):
    transform, material = add_mesh_entity(
        f"meshlet_{index:02d}_tri_{meshlet['triangles']:02d}",
        util.identity(),
        (meshlet["vertices"], meshlet["colors"], meshlet["normals"]),
        meshlet["indices"],
        BuiltInMaterial.PBR,
    )
    material.setUniformVariable("albedoColor", util.vec(1.0, 1.0, 1.0))
    material.setUniformVariable("metallic", 0.1)
    material.setUniformVariable("roughness", 0.55)
    material.setUniformVariable("ao", 1.0)
    material.setUniformVariable("ambientStr", 0.045)

    bound_vertices, bound_colors, bound_indices = create_bound_lines(
        meshlet["center"], meshlet["radius"] * 1.08, meshlet["color"]
    )
    bound_transform, bound_material = add_mesh_entity(
        f"meshlet_{index:02d}_bounds",
        util.identity(),
        (bound_vertices, bound_colors),
        bound_indices,
        BuiltInMaterial.COLOR,
        PrimitiveType.LINELIST,
    )

    render_items.append(
        {
            "meshlet": meshlet,
            "transform": transform,
            "material": material,
            "bound_transform": bound_transform,
            "bound_material": bound_material,
        }
    )


grid_vertices, grid_colors, grid_indices = create_grid()
grid_transform, grid_material = add_mesh_entity(
    "meshlet_reference_grid",
    util.identity(),
    (grid_vertices, grid_colors),
    grid_indices,
    BuiltInMaterial.COLOR,
    PrimitiveType.LINELIST,
)

renderUpdate = scene.world.createSystem(RenderRHISystem())
initUpdate = scene.world.createSystem(InitRHISystem())

scene.init(
    windowWidth=winWidth,
    windowHeight=winHeight,
    windowTitle="Elements RHI: Meshlet Imitation",
    clear_color=(0.022, 0.026, 0.032, 1.0),
)
scene.world.traverse_visit(initUpdate, scene.world.root)

camera = OrbitCameraController(target=(0.0, 0.0, 0.0), distance=6.4)
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
    base_model = util.rotate((0.0, 1.0, 0.0), elapsed * 10.0)
    explode_amount = 0.22 + 0.18 * (0.5 + 0.5 * math.sin(elapsed * 1.2))
    light_position = util.vec(
        3.2 * math.cos(elapsed * 0.55),
        2.7,
        3.2 * math.sin(elapsed * 0.55),
    )

    grid_material.setUniformVariable(
        "modelViewProj", projMat @ view @ grid_transform.trs
    )

    for item in render_items:
        offset = item["meshlet"]["explode_dir"] * explode_amount
        model = util.translate(offset[0], offset[1], offset[2]) @ base_model

        item["transform"].trs = model
        item["material"].setUniformVariable("modelViewProj", projMat @ view @ model)
        item["material"].setUniformVariable("model", model)
        item["material"].setUniformVariable("viewPos", eye)
        item["material"].setUniformVariable("lightPos", light_position)
        item["material"].setUniformVariable("lightColor", util.vec(1.0, 0.96, 0.88))
        item["material"].setUniformVariable("lightIntensity", 42.0)

        item["bound_transform"].trs = model
        item["bound_material"].setUniformVariable(
            "modelViewProj", projMat @ view @ model
        )

    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()
