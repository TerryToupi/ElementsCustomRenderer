from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

import Elements.pyECSS.System
from Elements.pyECSS.Component import Component, CompNullIterator, RenderMesh
from Elements.pyECSS.System import System

from .Enums import (
    BufferUsage,
    CompareOp,
    CullMode,
    FillMode,
    PrimitiveType,
    ShaderStage,
    TextureFormat,
    VertexElementFormat,
)
from .Resources.GraphicsPipeline import (
    GraphicsPipelineDescriptor,
    VertexAttribute,
    VertexBufferDescription,
)
from .Resources.Shader import ShaderDescriptor


SHADER_DIR = Path(__file__).with_name("Shaders")


class BuiltInMaterial(Enum):
    COLOR = "color_mvp"
    PHONG = "phong"
    PBR = "pbr"


@dataclass(frozen=True)
class ShaderSpec:
    vertex_binary: str
    fragment_binary: str
    vertex_uniform_buffers: int = 0
    fragment_uniform_buffers: int = 0


BUILTIN_SHADERS = {
    BuiltInMaterial.COLOR: ShaderSpec(
        vertex_binary="color_mvp.vert.spv.b64",
        fragment_binary="color_mvp.frag.spv.b64",
        vertex_uniform_buffers=1,
    ),
    BuiltInMaterial.PHONG: ShaderSpec(
        vertex_binary="phong.vert.spv.b64",
        fragment_binary="phong.frag.spv.b64",
        vertex_uniform_buffers=1,
        fragment_uniform_buffers=1,
    ),
    BuiltInMaterial.PBR: ShaderSpec(
        vertex_binary="pbr.vert.spv.b64",
        fragment_binary="pbr.frag.spv.b64",
        vertex_uniform_buffers=1,
        fragment_uniform_buffers=1,
    ),
}


class RHIMesh(Component):
    def __init__(
        self,
        name=None,
        type=None,
        id=None,
        attributes=None,
        index=None,
        primitive: PrimitiveType | int = PrimitiveType.TRIANGLELIST,
    ):
        super().__init__(name, type, id)
        self._attributes = attributes
        self._index = index
        self._primitive = primitive
        self.vertex_buffer_handle = None
        self.index_buffer_handle = None
        self.vertex_count = 0
        self.index_count = 0
        self.vertex_stride = 0
        self.vertex_buffer_descriptions: tuple[VertexBufferDescription, ...] = ()
        self.vertex_attributes: tuple[VertexAttribute, ...] = ()
        self.initialized = False

    @property
    def attributes(self):
        return self._attributes

    @attributes.setter
    def attributes(self, value):
        self._attributes = value

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = value

    @property
    def primitive(self):
        return self._primitive

    @primitive.setter
    def primitive(self, value):
        self._primitive = value

    def init_from_render_mesh(self, render_mesh: RenderMesh, resources) -> None:
        if self.initialized:
            return

        attributes = self._attributes or render_mesh.vertex_attributes
        indices = self._index or render_mesh.vertex_index
        vertex_data, attribute_layout = self._build_vertex_data(attributes)

        self.vertex_count = int(vertex_data.shape[0])
        self.vertex_stride = int(vertex_data.shape[1] * vertex_data.dtype.itemsize)
        self.vertex_buffer_descriptions = (
            VertexBufferDescription(slot=0, pitch=self.vertex_stride),
        )
        self.vertex_attributes = tuple(attribute_layout)
        self.vertex_buffer_handle = resources.create_buffer_with_data(
            np.ascontiguousarray(vertex_data),
            BufferUsage.VERTEX,
        )

        index_data = self._build_index_data(indices)
        if index_data is not None:
            self.index_count = int(index_data.size)
            self.index_buffer_handle = resources.create_buffer_with_data(
                np.ascontiguousarray(index_data),
                BufferUsage.INDEX,
            )

        self.initialized = True

    def layout_signature(self) -> tuple[Any, ...]:
        return (
            self.vertex_stride,
            tuple(self.vertex_buffer_descriptions),
            tuple(self.vertex_attributes),
        )

    def init(self):
        pass

    def update(self, **kwargs):
        pass

    def accept(self, system: Elements.pyECSS.System):
        if hasattr(system, "apply2RHIMesh"):
            system.apply2RHIMesh(self)

    def __iter__(self) -> CompNullIterator:
        return CompNullIterator(self)

    @staticmethod
    def _build_vertex_data(attributes) -> tuple[np.ndarray, list[VertexAttribute]]:
        if not attributes:
            raise ValueError("RHIMesh requires at least one vertex attribute")

        arrays = []
        layout = []
        offset = 0
        vertex_count = None

        for location, attribute in enumerate(attributes):
            if attribute is None or len(attribute) == 0:
                continue
            data = np.asarray(attribute, dtype=np.float32)
            if data.ndim == 1:
                data = data.reshape((-1, 1))
            if data.ndim != 2:
                raise ValueError("vertex attributes must be one or two dimensional")
            if vertex_count is None:
                vertex_count = data.shape[0]
            elif data.shape[0] != vertex_count:
                raise ValueError("all vertex attributes must have the same length")

            element_format = _vertex_format(data.shape[1])
            layout.append(
                VertexAttribute(
                    location=location,
                    buffer_slot=0,
                    format=element_format,
                    offset=offset,
                )
            )
            offset += data.shape[1] * data.dtype.itemsize
            arrays.append(np.ascontiguousarray(data))

        if not arrays:
            raise ValueError("RHIMesh received only empty vertex attributes")

        return np.ascontiguousarray(np.concatenate(arrays, axis=1)), layout

    @staticmethod
    def _build_index_data(index) -> np.ndarray | None:
        if index is None or len(index) == 0:
            return None
        if isinstance(index, (list, tuple)) and len(index) == 1:
            index = index[0]
        return np.asarray(index, dtype=np.uint32).reshape(-1)


class Material(Component):
    def __init__(
        self,
        shader: BuiltInMaterial | str = BuiltInMaterial.COLOR,
        name=None,
        type=None,
        id=None,
    ):
        super().__init__(name, type, id)
        self.shader = _material_key(shader)
        self.vertex_shader_handle = None
        self.fragment_shader_handle = None
        self.pipeline_handles: dict[tuple[Any, ...], Any] = {}
        self.uniforms: dict[str, Any] = {
            "modelViewProj": np.identity(4, dtype=np.float32),
            "model": np.identity(4, dtype=np.float32),
            "ambientColor": np.array([1.0, 1.0, 1.0], dtype=np.float32),
            "ambientStr": 0.3,
            "viewPos": np.array([0.0, 0.0, 1.0], dtype=np.float32),
            "lightPos": np.array([2.0, 5.5, 2.0], dtype=np.float32),
            "lightColor": np.array([1.0, 1.0, 1.0], dtype=np.float32),
            "lightIntensity": 0.8,
            "shininess": 0.4,
            "matColor": np.array([1.0, 1.0, 1.0], dtype=np.float32),
            "metallic": 0.0,
            "roughness": 0.5,
            "ao": 1.0,
        }

    def set_uniform(self, key: str, value: Any) -> None:
        self.uniforms[key] = value

    def setUniformVariable(self, key, value, **_legacy_flags) -> None:
        self.set_uniform(key, value)

    def prepare(self, context, mesh: RHIMesh):
        resources = context.resource_manager
        spec = BUILTIN_SHADERS[self.shader]

        if self.vertex_shader_handle is None:
            self.vertex_shader_handle = resources.create_shader(
                ShaderDescriptor.from_base64(
                    _read_shader(spec.vertex_binary),
                    stage=ShaderStage.VERTEX,
                    num_uniform_buffers=spec.vertex_uniform_buffers,
                )
            )
        if self.fragment_shader_handle is None:
            self.fragment_shader_handle = resources.create_shader(
                ShaderDescriptor.from_base64(
                    _read_shader(spec.fragment_binary),
                    stage=ShaderStage.FRAGMENT,
                    num_uniform_buffers=spec.fragment_uniform_buffers,
                )
            )

        fill_mode = FillMode.LINE if context.wireframe_mode else FillMode.FILL
        key = (
            self.shader,
            context.surface.texture_format,
            context.depth_format if context.depth_enabled else TextureFormat.INVALID,
            fill_mode,
            mesh.primitive,
            mesh.layout_signature(),
        )
        if key not in self.pipeline_handles:
            descriptor = GraphicsPipelineDescriptor(
                vertex_shader=self.vertex_shader_handle,
                fragment_shader=self.fragment_shader_handle,
                color_target_formats=(context.surface.texture_format,),
                vertex_buffer_descriptions=mesh.vertex_buffer_descriptions,
                vertex_attributes=mesh.vertex_attributes,
                primitive_type=mesh.primitive,
                fill_mode=fill_mode,
                cull_mode=CullMode.NONE,
                depth_stencil_format=(
                    context.depth_format
                    if context.depth_enabled
                    else TextureFormat.INVALID
                ),
                has_depth_stencil_target=context.depth_enabled,
                enable_depth_test=context.depth_enabled,
                enable_depth_write=context.depth_enabled,
                depth_compare_op=(
                    CompareOp.LESS if context.depth_enabled else CompareOp.INVALID
                ),
            )
            self.pipeline_handles[key] = resources.create_graphics_pipeline(descriptor)

        return resources.get_graphics_pipeline(self.pipeline_handles[key])

    def vertex_uniform_bytes(self) -> bytes:
        if self.shader in {BuiltInMaterial.PHONG, BuiltInMaterial.PBR}:
            return _matrix_bytes(self.uniforms["modelViewProj"]) + _matrix_bytes(
                self.uniforms["model"]
            )
        return _matrix_bytes(self.uniforms["modelViewProj"])

    def fragment_uniform_bytes(self) -> bytes:
        if self.shader is BuiltInMaterial.COLOR:
            return b""

        if self.shader is BuiltInMaterial.PHONG:
            values = [
                _vec4(self.uniforms["ambientColor"]),
                _vec4(self.uniforms["viewPos"]),
                _vec4(self.uniforms["lightPos"]),
                _vec4(self.uniforms["lightColor"]),
                _vec4(self.uniforms["matColor"]),
                np.array(
                    [
                        self.uniforms["ambientStr"],
                        self.uniforms["lightIntensity"],
                        self.uniforms["shininess"],
                        0.0,
                    ],
                    dtype=np.float32,
                ),
            ]
            return np.ascontiguousarray(np.concatenate(values)).tobytes()

        albedo = self.uniforms.get("albedoColor", self.uniforms["matColor"])
        values = [
            _vec4(self.uniforms["viewPos"]),
            _vec4(self.uniforms["lightPos"]),
            _vec4(self.uniforms["lightColor"]),
            _vec4(albedo),
            np.array(
                [
                    self.uniforms["metallic"],
                    self.uniforms["roughness"],
                    self.uniforms["ao"],
                    self.uniforms["lightIntensity"],
                ],
                dtype=np.float32,
            ),
            np.array(
                [
                    self.uniforms["ambientStr"],
                    0.0,
                    0.0,
                    0.0,
                ],
                dtype=np.float32,
            ),
        ]
        return np.ascontiguousarray(np.concatenate(values)).tobytes()

    @property
    def has_fragment_uniforms(self) -> bool:
        return BUILTIN_SHADERS[self.shader].fragment_uniform_buffers > 0

    def init(self):
        pass

    def update(self, **kwargs):
        pass

    def accept(self, system: Elements.pyECSS.System):
        if hasattr(system, "apply2Material"):
            system.apply2Material(self)

    def __iter__(self) -> CompNullIterator:
        return CompNullIterator(self)


class InitRHISystem(System):
    def __init__(self, context=None, name=None, type=None, id=None):
        super().__init__(name, type, id)
        self.context = context

    def apply2RHIMesh(self, mesh: RHIMesh, event=None):
        context = _resolve_context(self.context)
        self.context = context
        render_mesh = mesh.parent.getChildByType(RenderMesh.getClassName())
        if render_mesh is None:
            raise ValueError(f"RHIMesh on {mesh.parent.name} has no RenderMesh")
        mesh.init_from_render_mesh(render_mesh, context.resource_manager)


class RenderRHISystem(System):
    def __init__(self, context=None, name=None, type=None, id=None):
        super().__init__(name, type, id)
        self.context = context

    def apply2RHIMesh(self, mesh: RHIMesh, event=None):
        context = _resolve_context(self.context)
        self.context = context

        render_mesh = mesh.parent.getChildByType(RenderMesh.getClassName())
        material = mesh.parent.getChildByType(Material.getClassName())
        if render_mesh is None or material is None:
            return
        if not mesh.initialized:
            mesh.init_from_render_mesh(render_mesh, context.resource_manager)

        pipeline = material.prepare(context, mesh)
        command_buffer = context.command_buffer
        resources = context.resource_manager

        command_buffer.bind_graphics_pipeline(pipeline)
        command_buffer.push_vertex_uniform_data(0, material.vertex_uniform_bytes())
        if material.has_fragment_uniforms:
            command_buffer.push_fragment_uniform_data(0, material.fragment_uniform_bytes())
        command_buffer.bind_vertex_buffers(
            ((resources.get_buffer(mesh.vertex_buffer_handle), 0),)
        )

        if mesh.index_buffer_handle is not None:
            command_buffer.gpu_draw_indexed_instanced(
                None,
                None,
                resources.get_buffer(mesh.index_buffer_handle),
                mesh.index_count,
                1,
            )
        else:
            command_buffer.draw_primitives(mesh.vertex_count)


class RenderRHIStateSystem(System):
    def apply2RHIWindow(self, rhi_window, event=None):
        if event is None:
            return
        if event.name == "OnUpdateWireframe":
            rhi_window.wireframe_mode = event.value
        elif event.name == "OnUpdateCamera":
            rhi_window._myCamera = event.value


def _vertex_format(width: int) -> VertexElementFormat:
    formats = {
        1: VertexElementFormat.FLOAT,
        2: VertexElementFormat.FLOAT2,
        3: VertexElementFormat.FLOAT3,
        4: VertexElementFormat.FLOAT4,
    }
    if width not in formats:
        raise ValueError(f"unsupported vertex attribute width: {width}")
    return formats[width]


def _material_key(shader: BuiltInMaterial | str) -> BuiltInMaterial:
    if isinstance(shader, BuiltInMaterial):
        return shader
    normalized = str(shader).lower()
    for material in BuiltInMaterial:
        if material.value == normalized or material.name.lower() == normalized:
            return material
    raise ValueError(f"unknown built-in RHI material: {shader}")


def _read_shader(filename: str) -> str:
    return (SHADER_DIR / filename).read_text(encoding="ascii").strip()


def _matrix_bytes(matrix: Any) -> bytes:
    value = np.asarray(matrix, dtype=np.float32)
    if value.shape != (4, 4):
        raise ValueError("matrix uniforms must be 4x4")
    return np.ascontiguousarray(value.T).tobytes()


def _vec4(value: Any) -> np.ndarray:
    array = np.asarray(value, dtype=np.float32).reshape(-1)
    result = np.zeros(4, dtype=np.float32)
    result[: min(array.size, 4)] = array[:4]
    if array.size < 4:
        result[3] = 1.0
    return result


def _resolve_context(context):
    if context is not None:
        return context

    from .Scene import Scene

    scene = Scene()
    if scene.renderWindow is None:
        raise RuntimeError("RHI Scene must be initialized before RHI systems run")
    return scene.renderWindow
