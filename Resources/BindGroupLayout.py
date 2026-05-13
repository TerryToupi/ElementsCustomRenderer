from __future__ import annotations

from dataclasses import dataclass, field

from Enums import ShaderStage


@dataclass(frozen=True, slots=True)
class BindGroupLayoutEntryDescriptor:
    binding: int
    resource_type: str
    shader_stage: ShaderStage | int | None = None


@dataclass(slots=True)
class BindGroupLayoutDescriptor:
    entries: tuple[BindGroupLayoutEntryDescriptor, ...] = field(default_factory=tuple)
    label: str = ""


@dataclass(slots=True)
class BindGroupLayout:
    descriptor: BindGroupLayoutDescriptor
