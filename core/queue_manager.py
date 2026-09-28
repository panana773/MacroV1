from __future__ import annotations

from typing import Iterable


class QueueManager:
    def __init__(self) -> None:
        self._positions: list[tuple[int, int]] = []

    def add(self, x: int, y: int) -> None:
        self._positions.append((int(x), int(y)))

    def delete(self, index: int) -> bool:
        if 0 <= index < len(self._positions):
            del self._positions[index]
            return True
        return False

    def move_up(self, index: int) -> int:
        if 0 < index < len(self._positions):
            self._positions[index - 1], self._positions[index] = (
                self._positions[index],
                self._positions[index - 1],
            )
            return index - 1
        return index

    def move_down(self, index: int) -> int:
        if 0 <= index < len(self._positions) - 1:
            self._positions[index + 1], self._positions[index] = (
                self._positions[index],
                self._positions[index + 1],
            )
            return index + 1
        return index

    def clear(self) -> None:
        self._positions.clear()

    def set_positions(self, positions: Iterable[Iterable[int]]) -> None:
        cleaned: list[tuple[int, int]] = []

        for position in positions:
            values = list(position)

            if len(values) != 2:
                continue

            cleaned.append(
                (
                    int(values[0]),
                    int(values[1])
                )
            )

        self._positions = cleaned

    def items(self) -> list[tuple[int, int]]:
        return self._positions.copy()

    def snapshot(self) -> list[tuple[int, int]]:
        return self._positions.copy()

    def __len__(self) -> int:
        return len(self._positions)