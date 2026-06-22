from dataclasses import dataclass
from typing import Generic, TypeVar, cast

T = TypeVar("T")
_EMPTY = object()


class PoolError(LookupError):
    pass


@dataclass(frozen=True)
class PoolHandle(Generic[T]):
    index: int
    generation: int


class Pool(Generic[T]):
    def __init__(self):
        self._items: list[T | object] = []
        self._generations: list[int] = []
        self._free_indices: list[int] = []
        self._active_count = 0

    def __len__(self) -> int:
        return self._active_count

    def add(self, value: T) -> PoolHandle[T]:
        if self._free_indices:
            index = self._free_indices.pop()
            self._items[index] = value
        else:
            index = len(self._items)
            self._items.append(value)
            self._generations.append(0)

        self._active_count += 1
        return PoolHandle(index, self._generations[index])

    def valid(self, handle: PoolHandle[T]) -> bool:
        return (
            0 <= handle.index < len(self._items)
            and self._generations[handle.index] == handle.generation
            and self._items[handle.index] is not _EMPTY
        )

    def get(self, handle: PoolHandle[T]) -> T:
        if not self.valid(handle):
            raise PoolError(f"invalid or stale pool handle: {handle}")

        return cast(T, self._items[handle.index])

    def remove(self, handle: PoolHandle[T]) -> T:
        value = self.get(handle)
        self._items[handle.index] = _EMPTY
        self._generations[handle.index] += 1
        self._free_indices.append(handle.index)
        self._active_count -= 1
        return value

    def handles(self) -> list[PoolHandle[T]]:
        return [
            PoolHandle(index, self._generations[index])
            for index, item in enumerate(self._items)
            if item is not _EMPTY
        ]

    def clear(self) -> None:
        for index in range(len(self._items)):
            self._items[index] = _EMPTY
            self._generations[index] += 1

        self._free_indices = list(range(len(self._items)))
        self._active_count = 0
