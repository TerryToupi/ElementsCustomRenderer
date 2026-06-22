"""Minimal RHI graphics pipeline example.

This example avoids ECS on purpose. It shows the direct RHI flow:

1. Create a window, GPU device, surface, and resource manager.
2. Create shaders and a graphics pipeline.
3. Every frame: poll events, begin a render pass, bind the pipeline, draw.

The goal is not visual complexity. The goal is to see the important RHI objects
in the same order they are used by a real renderer.
"""

from pathlib import Path

from Elements.pyGLV.RHI import Key, QuitEvent, RHIWindow, WindowCloseEvent
from Elements.pyGLV.RHI.Enums import ShaderFormat, ShaderStage
from Elements.pyGLV.RHI.Resources.GraphicsPipeline import GraphicsPipelineDescriptor
from Elements.pyGLV.RHI.Resources.Shader import ShaderDescriptor


SHADER_DIR = Path(__file__).resolve().parents[2] / "pyGLV" / "RHI" / "Shaders"


def load_shader_blob(name: str) -> str:
    # The examples keep shader bytecode as base64 text files for portability.
    return (SHADER_DIR / name).read_text()


def shader_variant(window: RHIWindow, stem: str) -> tuple[str, ShaderFormat, str]:
    # SDL_GPU accepts different shader formats depending on the backend.
    # Metal uses MSL; Vulkan-style backends use SPIR-V.
    if window.device.shader_format == ShaderFormat.MSL:
        return load_shader_blob(f"{stem}.msl.b64"), ShaderFormat.MSL, "main0"
    return load_shader_blob(f"{stem}.spv.b64"), ShaderFormat.SPIRV, "main"


# RHIWindow creates the SDL window, SDL_GPU device, swapchain surface, and
# ResourceManager. For this first graphics example, that is enough setup.
window = RHIWindow(
    windowTitle="Elements RHI: basic graphics pipeline",
    clear_color=(0.04, 0.05, 0.07, 1.0),
    depth_enabled=False,
)
window.init()

resources = window.resource_manager

# The vertex shader uses gl_VertexIndex, so this pipeline needs no vertex buffer.
# That lets students focus on the pipeline and draw call first.
vertex_code, shader_format, entrypoint = shader_variant(window, "triangle.vert")
fragment_code, _, _ = shader_variant(window, "triangle.frag")

# Shaders are GPU resources. The descriptor tells SDL_GPU the stage, format, and
# entry point for the shader code.
vertex_shader = resources.create_shader(
    ShaderDescriptor.from_base64(
        vertex_code,
        stage=ShaderStage.VERTEX,
        format=shader_format,
        entrypoint=entrypoint,
    )
)
fragment_shader = resources.create_shader(
    ShaderDescriptor.from_base64(
        fragment_code,
        stage=ShaderStage.FRAGMENT,
        format=shader_format,
        entrypoint=entrypoint,
    )
)

# The graphics pipeline combines shaders plus fixed render state. This minimal
# pipeline has no vertex layout because the shader generates positions itself.
pipeline_handle = resources.create_graphics_pipeline(
    GraphicsPipelineDescriptor(
        vertex_shader=vertex_shader,
        fragment_shader=fragment_shader,
        color_target_formats=(window.surface.texture_format,),
    )
)
pipeline = resources.get_graphics_pipeline(pipeline_handle)

running = True
try:
    while running:
        # 1. Start the frame and collect input/window events.
        window.begin_frame()

        for event in window.poll_events():
            if isinstance(event, (QuitEvent, WindowCloseEvent)):
                running = False
        if window.input.was_key_pressed(Key.ESCAPE):
            running = False
        if not running:
            break

        # 2. Begin rendering. display() records surface acquisition and begins
        # a render pass that clears the swapchain texture.
        window.display()
        command_buffer = window.command_buffer

        # 3. Bind the pipeline and issue one draw call. The number 3 means
        # "run the vertex shader for three vertices".
        command_buffer.bind_graphics_pipeline(pipeline)
        command_buffer.draw_primitives(3)

        # 4. End the render pass and submit the recorded command buffer.
        window.display_post()
        window.end_frame()
finally:
    # Destroy RHI resources in the reverse direction of setup.
    window.shutdown()
