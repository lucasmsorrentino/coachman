"""Direções de movimento (Value Object)."""
from __future__ import annotations

from enum import Enum


class Direction(Enum):
    """As quatro direções do labirinto.

    A ORDEM DE DECLARAÇÃO IMPORTA: é a ordem de desempate do arcade quando
    duas saídas ficam à mesma distância do alvo de um fantasma
    (cima > esquerda > baixo > direita).
    """

    UP = (0, -1)
    LEFT = (-1, 0)
    DOWN = (0, 1)
    RIGHT = (1, 0)

    @property
    def dx(self) -> int:
        return self.value[0]

    @property
    def dy(self) -> int:
        return self.value[1]

    @property
    def opposite(self) -> "Direction":
        return _OPPOSITE[self]

    @property
    def is_horizontal(self) -> bool:
        return self.dy == 0

    def is_perpendicular_to(self, other: "Direction") -> bool:
        return self.is_horizontal != other.is_horizontal


_OPPOSITE = {
    Direction.UP: Direction.DOWN,
    Direction.DOWN: Direction.UP,
    Direction.LEFT: Direction.RIGHT,
    Direction.RIGHT: Direction.LEFT,
}

# Atalho usado pela IA: mesma ordem de prioridade da enum.
PRIORITY = tuple(Direction)
