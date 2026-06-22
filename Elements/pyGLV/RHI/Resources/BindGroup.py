from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BindGroupEntryDescriptor:
    binding: int
    resource: Any


@dataclass
class BindGroupDescriptor:
    layout: Any | None = None
    entries: tuple[BindGroupEntryDescriptor, ...] = field(default_factory=tuple)
    label: str = ""


@dataclass
class BindGroup:
    descriptor: BindGroupDescriptor
