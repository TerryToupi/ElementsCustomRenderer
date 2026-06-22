"""Minimal RHI compute pipeline example.

This example runs one compute dispatch and reads the result back to Python.
The shader writes index * index into an eight-element GPU buffer.

Unlike the graphics example, no image is drawn. Data flows like this:

Python creates GPU buffer -> compute shader writes buffer -> Python reads buffer.
"""

import base64
import struct
from pathlib import Path

from Elements.pyGLV.RHI import Device, ResourceManager, Window
from Elements.pyGLV.RHI.Enums import BufferUsage, ShaderFormat, WindowFlag
from Elements.pyGLV.RHI.Resources.Buffer import BufferDescriptor
from Elements.pyGLV.RHI.Resources.ComputePipeline import ComputePipelineDescriptor


SHADER_DIR = Path(__file__).resolve().parents[2] / "pyGLV" / "RHI" / "Shaders"
VALUE_COUNT = 8
THREADS_PER_WORKGROUP = 8


def load_compute_shader(device: Device) -> tuple[bytes, ShaderFormat, str]:
    # Use the shader format selected by Device. On macOS this is usually MSL.
    if device.shader_format == ShaderFormat.MSL:
        return (
            (SHADER_DIR / "compute_square.comp.msl").read_bytes(),
            ShaderFormat.MSL,
            "main0",
        )

    encoded = (SHADER_DIR / "compute_square.comp.spv.b64").read_text()
    return base64.b64decode(encoded), ShaderFormat.SPIRV, "main"


# SDL_GPU device creation requires SDL's video subsystem, so create a tiny hidden
# RHI window. No swapchain or render pass is needed for this compute-only example.
window = Window(
    title="Elements RHI compute setup",
    width=64,
    height=64,
    flags=WindowFlag.HIDDEN,
)
device = Device()
resources = ResourceManager(device)

try:
    # A compute pipeline is a single compute shader plus its resource layout.
    # This shader has one read-write storage buffer.
    shader_code, shader_format, entrypoint = load_compute_shader(device)
    pipeline_handle = resources.create_compute_pipeline(
        ComputePipelineDescriptor(
            code=shader_code,
            format=shader_format,
            entrypoint=entrypoint,
            num_readwrite_storage_buffers=1,
            threadcount_x=THREADS_PER_WORKGROUP,
            threadcount_y=1,
            threadcount_z=1,
        )
    )
    pipeline = resources.get_compute_pipeline(pipeline_handle)

    # The output buffer is visible to compute shaders. Each uint is 4 bytes.
    output_buffer_handle = resources.create_buffer(
        BufferDescriptor(
            size=VALUE_COUNT * 4,
            usage=BufferUsage.COMPUTE_STORAGE_READ | BufferUsage.COMPUTE_STORAGE_WRITE,
        )
    )
    output_buffer = resources.get_buffer(output_buffer_handle)

    # Record the compute commands through the RHI command buffer abstraction.
    command_buffer = device.acquire_command_buffer()

    # begin_compute_pass() binds read-write buffers for the pass. The shader
    # sees output_buffer at storage-buffer slot 0.
    command_buffer.begin_compute_pass((output_buffer,))
    command_buffer.bind_compute_pipeline(pipeline)

    # Dispatch one workgroup. The shader declares local_size_x = 8, so one
    # workgroup produces exactly VALUE_COUNT results.
    command_buffer.gpu_dispatch(None, (1, 1, 1))
    command_buffer.end_compute_pass()
    device.submit_command_buffer(command_buffer)

    # Wait for the GPU to finish before reading the buffer back on the CPU.
    device.wait_idle()
    raw_result = resources.download_buffer(output_buffer_handle)
    values = struct.unpack(f"{VALUE_COUNT}I", raw_result)

    print("GPU wrote:", values)
finally:
    resources.close()
    device.close()
    window.close()
