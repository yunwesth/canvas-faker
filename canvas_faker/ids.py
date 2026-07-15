"""ID allocation and cross-table registries used during generation."""
from __future__ import annotations

import uuid as _uuid


class IdAllocator:
    """Issues sequential int64 IDs per table, starting at 1."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = {}

    def next(self, table: str) -> int:
        n = self._counters.get(table, 0) + 1
        self._counters[table] = n
        return n

    def peek(self, table: str) -> int:
        return self._counters.get(table, 0)


def new_uuid() -> str:
    return str(_uuid.uuid4())


class Registry:
    """Holds lists of generated IDs so FK columns can pick valid targets."""

    def __init__(self) -> None:
        self._ids: dict[str, list[int | str]] = {}

    def register(self, key: str, id_: int | str) -> None:
        self._ids.setdefault(key, []).append(id_)

    def ids(self, key: str) -> list[int | str]:
        return self._ids.get(key, [])

    def has(self, key: str) -> bool:
        return bool(self._ids.get(key))
