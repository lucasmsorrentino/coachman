"""Criação das entidades de uma fase -- padrão **Factory**.

Herdado da versão original do projeto (``EntityFactory.py``), agora mais
completo: a fábrica é o único lugar que sabe *montar* uma cadeira -- qual
personalidade (Strategy) ela usa, qual é o seu canto de dispersão, onde ela
nasce na casa. O resto do jogo recebe objetos prontos.

(Tecnicamente é uma *Simple Factory*, a variação mais comum do Factory
Method do GoF, p. 107: um método que encapsula ``new``.)
"""
from __future__ import annotations

from dataclasses import dataclass

from ..config import TILE
from ..world.maze import Maze, Tile
from .coachman import CoachMan
from .ghost import Ghost, GhostWorld
from .targeting import AmbushTargeting, PokeyTargeting, ShadowTargeting, TargetingStrategy, WhimsicalTargeting


@dataclass(frozen=True)
class GhostProfile:
    name: str
    strategy: type[TargetingStrategy]
    corner: str  # canto de dispersão
    home_slot: int  # -1 esquerda, 0 centro, 1 direita (na casa)
    starts_outside: bool


# Ordem importa: é a ordem de saída da casa (Pinky, Inky, Clyde).
PROFILES = (
    GhostProfile("blinky", ShadowTargeting, "top-right", 0, True),
    GhostProfile("pinky", AmbushTargeting, "top-left", 0, False),
    GhostProfile("inky", WhimsicalTargeting, "bottom-right", -1, False),
    GhostProfile("clyde", PokeyTargeting, "bottom-left", 1, False),
)


def scatter_corner(maze: Maze, corner: str) -> Tile:
    """Cantos *fora* do labirinto, como no arcade: inalcançáveis, então a
    cadeira fica dando voltas no bloco mais próximo."""
    return {
        "top-right": (maze.cols - 3, -3),
        "top-left": (2, -3),
        "bottom-right": (maze.cols - 1, maze.rows + 1),
        "bottom-left": (0, maze.rows + 1),
    }[corner]


class EntityFactory:
    def __init__(self, maze: Maze) -> None:
        self.maze = maze

    def create_coachman(self) -> CoachMan:
        x, y = self.maze.definition.pacman_start
        return CoachMan(self.maze, x * TILE, y * TILE)

    def create_ghosts(self, world: GhostWorld) -> list[Ghost]:
        return [
            Ghost(
                name=p.name,
                maze=self.maze,
                world=world,
                strategy=p.strategy(),
                scatter_tile=scatter_corner(self.maze, p.corner),
                home_slot=p.home_slot,
                starts_outside=p.starts_outside,
            )
            for p in PROFILES
        ]
