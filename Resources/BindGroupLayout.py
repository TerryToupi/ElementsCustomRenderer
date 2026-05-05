from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class BindGroupLayoutEntryDescriptor:
    binding: int
    resource_type: str
    shader_stage: int | None = None


@dataclass(slots=True)
class BindGroupLayoutDescriptor:
    entries: tuple[BindGroupLayoutEntryDescriptor, ...] = field(default_factory=tuple)
    label: str = ""


@dataclass(slots=True)
class BindGroupLayout:
    descriptor: BindGroupLayoutDescriptor
