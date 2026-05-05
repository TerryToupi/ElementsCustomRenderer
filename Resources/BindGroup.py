from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class BindGroupEntryDescriptor:
    binding: int
    resource: Any


@dataclass(slots=True)
class BindGroupDescriptor:
    layout: Any | None = None
    entries: tuple[BindGroupEntryDescriptor, ...] = field(default_factory=tuple)
    label: str = ""


@dataclass(slots=True)
class BindGroup:
    descriptor: BindGroupDescriptor
