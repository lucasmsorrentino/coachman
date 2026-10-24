"""Base das entidades que andam no labirinto -- padrão **Template Method**
(GoF, "Template Method", p. 325).

``Actor.update()`` é o *algoritmo-esqueleto* do movimento estilo arcade,
igual para o Coach-Man e para as cadeiras:

1. respeita pausas (``freeze``);
2. ``before_move()``      -> gancho (o Coach-Man trata a curva antecipada);
3. anda ``speed() * BASE_SPEED`` pixels, parando *exatamente* no centro de
   cada tile para chamar ``choose_direction_at_center()`` -> gancho (o
   jogador decide pela tecla; a cadeira, pela IA);
4. ``after_move()``       -> gancho.

As subclasses preenchem só os ganchos; o "como andar" fica num único lugar.

Por que parar no centro do tile? No arcade, toda decisão de direção acontece
no centro dos tiles; um personagem rápido poderia "pular" o centro dentro de
um quadro e perder a curva. Aqui o deslocamento é quebrado em pedaços que
nunca ultrapassam o próximo centro.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..config import BASE_SPEED, TILE
from ..world.direction import Direction
from ..world.maze import Maze, Tile

EPS = 1e-6


class Actor(ABC):
    def __init__(self, maze: Maze, x: float, y: float, direction: Direction) -> None:
        self.maze = maze
        self.x, self.y = x, y
        self.direction = direction
        self.freeze = 0  # quadros parados
        self.moved = 0.0  # pixels andados no último quadro (para animação)

    # ------------------------------------------------------------------ posição
    @property
    def tile(self) -> Tile:
        return int(self.x // TILE), int(self.y // TILE)

    @property
    def maze_tile(self) -> Tile:
        """Tile com o *wrap* do túnel aplicado (sempre dentro do mapa)."""
        c, r = self.tile
        return self.maze.wrap_col(c), r

    def place(self, x: float, y: float, direction: Direction) -> None:
        self.x, self.y, self.direction = x, y, direction

    # ------------------------------------------------------------------ template method
    def update(self) -> None:
        self.moved = 0.0
        if self.freeze > 0:
            self.freeze -= 1
            return
        self.before_move()
        self.move(self.speed() * BASE_SPEED)
        self.after_move()

    @abstractmethod
    def speed(self) -> float:
        """Fração da velocidade máxima neste quadro."""

    @abstractmethod
    def choose_direction_at_center(self) -> Direction | None:
        """Direção a seguir a partir do centro do tile atual (None = parar)."""

    def before_move(self) -> None:
        """Gancho opcional."""

    def after_move(self) -> None:
        """Gancho opcional."""

    # ------------------------------------------------------------------ mecânica
    def move(self, distance: float) -> None:
        self.moved = self._align_cross_axis(distance)
        while distance > EPS:
            ahead = self._distance_to_next_center()
            if ahead <= EPS:
                self._snap_main_axis()
                new_direction = self.choose_direction_at_center()
                if new_direction is None:
                    break  # parado contra a parede
                self.direction = new_direction
                ahead = TILE
            step = min(distance, ahead)
            self.x += self.direction.dx * step
            self.y += self.direction.dy * step
            distance -= step
            self.moved += step
            self._wrap_tunnel()

    def _center_of_current_tile(self) -> tuple[float, float]:
        c, r = self.tile
        return (c + 0.5) * TILE, (r + 0.5) * TILE

    def _distance_to_next_center(self) -> float:
        cx, cy = self._center_of_current_tile()
        d = (cx - self.x) * self.direction.dx + (cy - self.y) * self.direction.dy
        if d < -EPS:  # já passou do centro deste tile: o próximo está 1 tile adiante
            d += TILE
        return max(0.0, d)

    def _snap_main_axis(self) -> None:
        cx, cy = self._center_of_current_tile()
        if self.direction.is_horizontal:
            self.x = cx
        else:
            self.y = cy

    def _align_cross_axis(self, distance: float) -> float:
        """Puxa o eixo perpendicular para o centro (curva em diagonal)."""
        cx, cy = self._center_of_current_tile()
        if self.direction.is_horizontal:
            delta = max(-distance, min(distance, cy - self.y))
            self.y += delta
        else:
            delta = max(-distance, min(distance, cx - self.x))
            self.x += delta
        return abs(delta)

    def _wrap_tunnel(self) -> None:
        width = self.maze.cols * TILE
        if self.x < -TILE / 2:
            self.x += width
        elif self.x >= width + TILE / 2:
            self.x -= width
