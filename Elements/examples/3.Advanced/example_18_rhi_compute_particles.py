"""RHI compute + graphics example: GPU particle swirl.

This is a teaching example for the full data flow:

1. CPU creates initial particle positions and velocities.
2. Particle data is uploaded once into a GPU storage buffer.
3. A compute shader updates that same buffer every frame.
4. A graphics shader reads the updated buffer and draws the particles.
5. The CPU never reads particle data back during animation.

The visual result is a swirling cloud of GPU-updated particles.
"""

import base64
import math
import struct
import time
from pathlib import Path

import numpy as np

from Elements.pyGLV.RHI import Key, QuitEvent, RHIWindow, WindowCloseEvent
from Elements.pyGLV.RHI.Enums import (
    BufferUsage,
    PrimitiveType,
    ShaderFormat,
    ShaderStage,
)
from Elements.pyGLV.RHI.Resources.Buffer import BufferDescriptor
from Elements.pyGLV.RHI.Resources.ComputePipeline import ComputePipelineDescriptor
from Elements.pyGLV.RHI.Resources.GraphicsPipeline import GraphicsPipelineDescriptor
from Elements.pyGLV.RHI.Resources.Shader import ShaderDescriptor


SHADER_DIR = Path(__file__).resolve().parents[2] / "pyGLV" / "RHI" / "Shaders"
PARTICLE_COUNT = 4096
THREADS_PER_WORKGROUP = 128


def load_shader_bytes(device, stem: str) -> tuple[bytes, ShaderFormat, str]:
    if device.shader_format == ShaderFormat.MSL:
        return (SHADER_DIR / f"{stem}.msl").read_bytes(), ShaderFormat.MSL, "main0"

    encoded = (SHADER_DIR / f"{stem}.spv.b64").read_text()
    return base64.b64decode(encoded), ShaderFormat.SPIRV, "main"


def create_initial_particles(count: int) -> np.ndarray:
    rng = np.random.default_rng(seed=7)
    angles = rng.uniform(0.0, math.tau, count)
    radii = np.sqrt(rng.uniform(0.02, 0.9, count))

    positions = np.zeros((count, 4), dtype=np.float32)
    positions[:, 0] = np.cos(angles) * radii
    positions[:, 1] = np.sin(angles) * radii
    positions[:, 3] = 1.0

    velocities = np.zeros((count, 4), dtype=np.float32)
    velocities[:, 0] = -np.sin(angles) * 0.18
    velocities[:, 1] = np.cos(angles) * 0.18

    particles = np.zeros((count, 8), dtype=np.float32)
    particles[:, 0:4] = positions
    particles[:, 4:8] = velocities
    return particles


window = RHIWindow(
    windowWidth=1280,
    windowHeight=800,
    windowTitle="Elements RHI: compute-driven particles",
    clear_color=(0.015, 0.018, 0.028, 1.0),
    depth_enabled=False,
)
window.init()

device = window.device
resources = window.resource_manager

particle_data = create_initial_particles(PARTICLE_COUNT)
particle_buffer_handle = resources.create_buffer_with_data(
    particle_data,
    BufferUsage.GRAPHICS_STORAGE_READ
    | BufferUsage.COMPUTE_STORAGE_READ
    | BufferUsage.COMPUTE_STORAGE_WRITE,
)
particle_buffer = resources.get_buffer(particle_buffer_handle)

# Indexed drawing lets the vertex shader use gl_VertexIndex to choose a particle.
particle_indices_handle = resources.create_buffer_with_data(
    np.arange(PARTICLE_COUNT, dtype=np.uint32),
    BufferUsage.INDEX,
)
particle_indices = resources.get_buffer(particle_indices_handle)

compute_code, compute_format, compute_entrypoint = load_shader_bytes(
    device,
    "compute_particles.comp",
)
compute_pipeline_handle = resources.create_compute_pipeline(
    ComputePipelineDescriptor(
        code=compute_code,
        format=compute_format,
        entrypoint=compute_entrypoint,
        num_readwrite_storage_buffers=1,
        num_uniform_buffers=1,
        threadcount_x=THREADS_PER_WORKGROUP,
        threadcount_y=1,
        threadcount_z=1,
    )
)
compute_pipeline = resources.get_compute_pipeline(compute_pipeline_handle)

vertex_code, shader_format, graphics_entrypoint = load_shader_bytes(
    device,
    "compute_particles.vert",
)
fragment_code, _, _ = load_shader_bytes(device, "compute_particles.frag")

vertex_shader = resources.create_shader(
    ShaderDescriptor(
        code=vertex_code,
        stage=ShaderStage.VERTEX,
        format=shader_format,
        entrypoint=graphics_entrypoint,
        num_storage_buffers=1,
    )
)
fragment_shader = resources.create_shader(
    ShaderDescriptor(
        code=fragment_code,
        stage=ShaderStage.FRAGMENT,
        format=shader_format,
        entrypoint=graphics_entrypoint,
    )
)

graphics_pipeline_handle = resources.create_graphics_pipeline(
    GraphicsPipelineDescriptor(
        vertex_shader=vertex_shader,
        fragment_shader=fragment_shader,
        color_target_formats=(window.surface.texture_format,),
        primitive_type=PrimitiveType.POINTLIST,
    )
)
graphics_pipeline = resources.get_graphics_pipeline(graphics_pipeline_handle)

workgroup_count = math.ceil(PARTICLE_COUNT / THREADS_PER_WORKGROUP)
start_time = time.perf_counter()
last_time = start_time
running = True

try:
    while running:
        # Start the frame and handle window/input events before GPU work.
        window.begin_frame()
        for event in window.poll_events():
            if isinstance(event, (QuitEvent, WindowCloseEvent)):
                running = False
        if window.input.was_key_pressed(Key.ESCAPE):
            running = False
        if not running:
            break

        now = time.perf_counter()
        dt = min(now - last_time, 1.0 / 30.0)
        last_time = now
        elapsed = now - start_time

        # The compute pass updates particle positions directly on the GPU.
        command_buffer = device.acquire_command_buffer()
        command_buffer.begin_compute_pass((particle_buffer,))
        command_buffer.bind_compute_pipeline(compute_pipeline)
        command_buffer.push_compute_uniform_data(
            0,
            struct.pack("4f", dt, elapsed, float(PARTICLE_COUNT), 0.0),
        )
        command_buffer.gpu_dispatch(None, (workgroup_count, 1, 1))
        command_buffer.end_compute_pass()

        # The graphics pass reads the same particle buffer and turns each
        # particle into a point on screen. No CPU readback is needed each frame.
        window.display()
        command_buffer.bind_graphics_pipeline(graphics_pipeline)
        command_buffer.gpu_draw_indexed_instanced(
            particle_buffer,
            None,
            particle_indices,
            PARTICLE_COUNT,
            1,
        )
        window.display_post()
        window.end_frame()
finally:
    window.shutdown()
