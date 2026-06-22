"""RHI compute + graphics example: path-traced black hole volume.

This is an advanced teaching example for a common modern rendering pattern:

1. A compute shader ray-marches a scene into an HDR texture.
2. The same compute pass stores temporal history in a second HDR texture.
3. A graphics pass draws one fullscreen triangle.
4. The fragment shader samples the HDR texture and tone-maps it to the window.

The CPU never draws black-hole geometry. It only updates camera parameters and
records GPU commands. The image is produced by the compute shader.
"""

import base64
import math
import struct
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Elements.pyGLV.RHI import (
    Key,
    MouseButton,
    QuitEvent,
    RHIWindow,
    WindowCloseEvent,
)
from Elements.pyGLV.RHI.Enums import (
    Filter,
    PrimitiveType,
    SamplerAddressMode,
    ShaderFormat,
    ShaderStage,
    TextureFormat,
    TextureUsage,
)
from Elements.pyGLV.RHI.Resources.ComputePipeline import ComputePipelineDescriptor
from Elements.pyGLV.RHI.Resources.GraphicsPipeline import GraphicsPipelineDescriptor
from Elements.pyGLV.RHI.Resources.Sampler import SamplerDescriptor
from Elements.pyGLV.RHI.Resources.Shader import ShaderDescriptor
from Elements.pyGLV.RHI.Resources.Texture import TextureDescriptor


SHADER_DIR = Path(__file__).resolve().parents[2] / "pyGLV" / "RHI" / "Shaders"

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
RENDER_WIDTH = 960
RENDER_HEIGHT = 540
WORKGROUP_SIZE_X = 8
WORKGROUP_SIZE_Y = 8
EXPOSURE = 1.25
ACCUMULATION_ENABLED = True


def load_shader_bytes(device, stem: str) -> tuple[bytes, ShaderFormat, str]:
    """Load the shader variant that matches the active SDL_GPU backend."""
    if device.shader_format == ShaderFormat.MSL:
        return (SHADER_DIR / f"{stem}.msl").read_bytes(), ShaderFormat.MSL, "main0"

    encoded = (SHADER_DIR / f"{stem}.spv.b64").read_text()
    return base64.b64decode(encoded), ShaderFormat.SPIRV, "main"


def normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(component * component for component in vector))
    if length <= 0.00001:
        return 0.0, 0.0, 0.0
    return tuple(component / length for component in vector)


def subtract(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> tuple[float, float, float]:
    return left[0] - right[0], left[1] - right[1], left[2] - right[2]


def cross(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def orbit_camera(
    yaw: float,
    pitch: float,
    distance: float,
) -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]:
    """Return position plus forward/right/up vectors for a camera orbit."""
    cos_pitch = math.cos(pitch)
    position = (
        math.sin(yaw) * cos_pitch * distance,
        math.sin(pitch) * distance,
        math.cos(yaw) * cos_pitch * distance,
    )
    target = (0.0, 0.0, 0.0)
    world_up = (0.0, 1.0, 0.0)

    forward = normalize(subtract(target, position))
    right = normalize(cross(forward, world_up))
    up = normalize(cross(right, forward))
    return position, forward, right, up


def pack_trace_uniforms(
    camera_position: tuple[float, float, float],
    forward: tuple[float, float, float],
    right: tuple[float, float, float],
    up: tuple[float, float, float],
    elapsed_time: float,
    accumulation_frame: int,
) -> bytes:
    """Pack four vec4 values. The shader uses vec4s to stay std140-friendly."""
    return struct.pack(
        "16f",
        camera_position[0],
        camera_position[1],
        camera_position[2],
        elapsed_time,
        forward[0],
        forward[1],
        forward[2],
        float(accumulation_frame),
        right[0],
        right[1],
        right[2],
        EXPOSURE,
        1.0 if ACCUMULATION_ENABLED else 0.0,
        up[0],
        up[1],
        up[2],
    )


window = RHIWindow(
    windowWidth=WINDOW_WIDTH,
    windowHeight=WINDOW_HEIGHT,
    windowTitle="Elements RHI: compute path-traced black hole",
    clear_color=(0.0, 0.0, 0.0, 1.0),
    depth_enabled=False,
)
window.init()

device = window.device
resources = window.resource_manager

# The compute shader writes HDR radiance here. The graphics pass samples it.
hdr_usage = (
    TextureUsage.SAMPLER
    | TextureUsage.COMPUTE_STORAGE_READ
    | TextureUsage.COMPUTE_STORAGE_WRITE
    | TextureUsage.COMPUTE_STORAGE_SIMULTANEOUS_READ_WRITE
)
current_texture_handle = resources.create_texture(
    TextureDescriptor(
        width=RENDER_WIDTH,
        height=RENDER_HEIGHT,
        format=TextureFormat.R16G16B16A16_FLOAT,
        usage=hdr_usage,
    )
)
history_texture_handle = resources.create_texture(
    TextureDescriptor(
        width=RENDER_WIDTH,
        height=RENDER_HEIGHT,
        format=TextureFormat.R16G16B16A16_FLOAT,
        usage=hdr_usage,
    )
)
current_texture = resources.get_texture(current_texture_handle)
history_texture = resources.get_texture(history_texture_handle)

linear_sampler_handle = resources.create_sampler(
    SamplerDescriptor(
        min_filter=Filter.LINEAR,
        mag_filter=Filter.LINEAR,
        address_mode_u=SamplerAddressMode.CLAMP_TO_EDGE,
        address_mode_v=SamplerAddressMode.CLAMP_TO_EDGE,
        address_mode_w=SamplerAddressMode.CLAMP_TO_EDGE,
    )
)
linear_sampler = resources.get_sampler(linear_sampler_handle)

# Compute pipeline: ray-march into current_texture and update history_texture.
compute_code, compute_format, compute_entrypoint = load_shader_bytes(
    device,
    "black_hole_trace.comp",
)
compute_pipeline_handle = resources.create_compute_pipeline(
    ComputePipelineDescriptor(
        code=compute_code,
        format=compute_format,
        entrypoint=compute_entrypoint,
        num_readwrite_storage_textures=2,
        num_uniform_buffers=1,
        threadcount_x=WORKGROUP_SIZE_X,
        threadcount_y=WORKGROUP_SIZE_Y,
        threadcount_z=1,
    )
)
compute_pipeline = resources.get_compute_pipeline(compute_pipeline_handle)

# Graphics pipeline: draw one fullscreen triangle and tone-map the HDR texture.
vertex_code, shader_format, graphics_entrypoint = load_shader_bytes(
    device,
    "black_hole_tonemap.vert",
)
fragment_code, _, _ = load_shader_bytes(device, "black_hole_tonemap.frag")

vertex_shader = resources.create_shader(
    ShaderDescriptor(
        code=vertex_code,
        stage=ShaderStage.VERTEX,
        format=shader_format,
        entrypoint=graphics_entrypoint,
    )
)
fragment_shader = resources.create_shader(
    ShaderDescriptor(
        code=fragment_code,
        stage=ShaderStage.FRAGMENT,
        format=shader_format,
        entrypoint=graphics_entrypoint,
        num_samplers=1,
    )
)
graphics_pipeline_handle = resources.create_graphics_pipeline(
    GraphicsPipelineDescriptor(
        vertex_shader=vertex_shader,
        fragment_shader=fragment_shader,
        color_target_formats=(window.surface.texture_format,),
        primitive_type=PrimitiveType.TRIANGLELIST,
    )
)
graphics_pipeline = resources.get_graphics_pipeline(graphics_pipeline_handle)

workgroups_x = math.ceil(RENDER_WIDTH / WORKGROUP_SIZE_X)
workgroups_y = math.ceil(RENDER_HEIGHT / WORKGROUP_SIZE_Y)

yaw = 0.45
pitch = 0.18
distance = 7.0
accumulation_frame = 1
start_time = time.perf_counter()
running = True

try:
    while running:
        # Poll input before recording GPU commands. Input changes reset temporal
        # accumulation because history from a different camera would smear.
        window.begin_frame()
        for event in window.poll_events():
            if isinstance(event, (QuitEvent, WindowCloseEvent)):
                running = False
        if window.input.was_key_pressed(Key.ESCAPE):
            running = False
        if not running:
            break

        camera_changed = False
        if window.input.is_mouse_button_down(MouseButton.RIGHT):
            dx, dy = window.input.mouse_delta
            yaw -= dx * 0.006
            pitch = max(-0.95, min(0.95, pitch - dy * 0.006))
            camera_changed = camera_changed or abs(dx) > 0.0 or abs(dy) > 0.0

        _, wheel_y = window.input.mouse_wheel
        if abs(wheel_y) > 0.0:
            distance = max(3.0, min(13.0, distance - wheel_y * 0.55))
            camera_changed = True

        orbit_speed = 0.018
        zoom_speed = 0.055
        if window.input.is_key_down(Key.LEFT):
            yaw += orbit_speed
            camera_changed = True
        if window.input.is_key_down(Key.RIGHT):
            yaw -= orbit_speed
            camera_changed = True
        if window.input.is_key_down(Key.UP):
            pitch = min(0.95, pitch + orbit_speed)
            camera_changed = True
        if window.input.is_key_down(Key.DOWN):
            pitch = max(-0.95, pitch - orbit_speed)
            camera_changed = True
        if window.input.is_key_down(Key.W):
            distance = max(3.0, distance - zoom_speed)
            camera_changed = True
        if window.input.is_key_down(Key.S):
            distance = min(13.0, distance + zoom_speed)
            camera_changed = True

        if camera_changed:
            accumulation_frame = 1

        elapsed = time.perf_counter() - start_time
        camera_position, forward, right, up = orbit_camera(yaw, pitch, distance)
        trace_uniforms = pack_trace_uniforms(
            camera_position,
            forward,
            right,
            up,
            elapsed,
            accumulation_frame,
        )

        command_buffer = device.acquire_command_buffer()

        # Compute pass: each workgroup shades an 8x8 tile of the HDR texture.
        command_buffer.begin_compute_pass(
            storage_textures=(current_texture, history_texture),
        )
        command_buffer.bind_compute_pipeline(compute_pipeline)
        command_buffer.push_compute_uniform_data(0, trace_uniforms)
        command_buffer.gpu_dispatch(None, (workgroups_x, workgroups_y, 1))
        command_buffer.end_compute_pass()

        # Graphics pass: one fullscreen triangle samples the compute result.
        window.display()
        command_buffer.bind_graphics_pipeline(graphics_pipeline)
        command_buffer.bind_fragment_samplers(((current_texture, linear_sampler),))
        command_buffer.draw_primitives(3)
        window.display_post()
        window.end_frame()

        accumulation_frame += 1
finally:
    window.shutdown()
