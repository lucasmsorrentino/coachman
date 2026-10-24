"""Cadeira voadora (o "fantasma" deste jogo).

É o *Context* de dois padrões ao mesmo tempo:

* **State** -- ``self.state`` decide velocidade e direção (ghost_states.py);
* **Strategy** -- ``self.strategy`` decide o alvo na perseguição (targeting.py).

O movimento no labirinto reaproveita o Template Method de ``Actor``.
"""
from __future__ import annotations

import random
from typing import Protocol

from ..levels import LevelSpec
from ..world.direction import Direction
from ..world.maze import Maze, Tile
from . import ghost_states as states
from .actor import Actor
from .targeting import TargetContext, TargetingStrategy


class GhostWorld(Protocol):
    """O que a cadeira precisa saber do mundo (mantém o acoplamento baixo)."""

    spec: LevelSpec
    rng: random.Random

    def target_context(self, ghost: "Ghost") -> TargetContext: ...
    def global_mode_state(self) -> states.GhostState: ...
    def elroy_level(self, ghost: "Ghost") -> int: ...
    def ghost_speed(self, ghost: "Ghost") -> float: ...


class Ghost(Actor):
    SPIN_FRAMES = 8

    def __init__(
        self,
        name: str,
        maze: Maze,
        world: GhostWorld,
        strategy: TargetingStrategy,
        scatter_tile: Tile,
        home_slot: int,
        starts_outside: bool,
    ) -> None:
        super().__init__(maze, 0, 0, Direction.LEFT)
        self.name = name
        self.world = world
        self.strategy = strategy
        self.scatter_tile = scatter_tile
        self.home_slot = home_slot
        self.starts_outside = starts_outside
        self.state: states.GhostState = states.IN_HOUSE
        self.frightened = False
        self.exit_right = False
        self.target: Tile | None = None
        self.spin = 0.0
        self.reset()

    # ------------------------------------------------------------------ ciclo de vida
    @property
    def home_x(self) -> float:
        return self.maze.house_slot_x(self.home_slot)

    def reset(self) -> None:
        """Volta à posição inicial (começo de fase ou após o Coach-Man morrer)."""
        self.frightened = False
        self.exit_right = False
        self.target = None
        self.freeze = 0
        if self.starts_outside:
            self.place(self.maze.house_center_x, self.maze.house_exit_y, Direction.LEFT)
            self.state = states.SCATTER
        else:
            # Pinky começa olhando para baixo; Inky e Clyde, para cima (arcade)
            facing = Direction.DOWN if self.home_slot == 0 else Direction.UP
            self.place(self.home_x, self.maze.house_inside_y, facing)
            self.state = states.IN_HOUSE

    def change_state(self, state: states.GhostState) -> None:
        self.state = state
        state.enter(self)

    def release(self) -> None:
        if self.state is states.IN_HOUSE:
            self.change_state(states.LEAVING_HOUSE)

    def revive(self) -> None:
        self.frightened = False
        self.change_state(states.LEAVING_HOUSE)

    def reverse(self) -> None:
        self.direction = self.direction.opposite

    @property
    def in_house(self) -> bool:
        return self.state in (states.IN_HOUSE, states.LEAVING_HOUSE, states.ENTERING_HOUSE)

    @property
    def roaming(self) -> bool:
        """Em dispersão ou perseguição (sujeita às trocas de modo)."""
        return self.state in (states.SCATTER, states.CHASE)

    # ------------------------------------------------------------------ atualização
    def update(self) -> None:
        self.state.update(self)
        self.spin += 0.5 if self.state is states.EATEN else 0.2

    def move_in_maze(self) -> None:
        Actor.update(self)

    # ganchos do Template Method (delegados ao State)
    def speed(self) -> float:
        return self.state.speed(self)

    def choose_direction_at_center(self) -> Direction | None:
        return self.state.choose_direction(self)

    # ------------------------------------------------------------------ desenho
    @property
    def spin_frame(self) -> int:
        return int(self.spin) % self.SPIN_FRAMES

    def __repr__(self) -> str:
        return f"Ghost({self.name}, {self.state}, tile={self.tile})"

