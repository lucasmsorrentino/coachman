"""Modo "RAIO-X" (tecla TAB): mostra a IA das cadeiras em tempo real.

Desenha o tile-alvo de cada cadeira e a linha até ele, além dos elementos
geométricos de cada personalidade:

* Pinky -- a seta do Coach-Man até 4 tiles à frente;
* Inky  -- o ponto "2 à frente" e o vetor dobrado a partir do Blinky;
* Clyde -- o círculo de 8 tiles: dentro dele, ela desiste e vai para o canto.

É a melhor forma de *ver* o que está explicado em ``docs/FANTASMAS.md``.
"""
from __future__ import annotations

import pygame

from ..actors import ghost_states as gs
from ..actors.targeting import PokeyTargeting, tiles_ahead
from ..config import MAZE_Y, TILE
from ..core.assets import AssetLibrary
from ..world.world import World
from .text import draw_text

GHOST_COLORS = {
    "blinky": (255, 40, 40),
    "pinky": (255, 150, 210),
    "inky": (40, 240, 240),
    "clyde": (255, 184, 82),
}
MODE_NAMES = {"scatter": "DISPERSAO", "chase": "PERSEGUICAO"}


def _center(tile: tuple[int, int]) -> tuple[int, int]:
    return tile[0] * TILE + TILE // 2, tile[1] * TILE + TILE // 2 + MAZE_Y


def draw_debug(surface: pygame.Surface, assets: AssetLibrary, world: World) -> None:
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pac = world.coachman
    pac_center = _center(pac.maze_tile)

    for ghost in world.ghosts:
        color = GHOST_COLORS[ghost.name]
        if ghost.state not in (gs.SCATTER, gs.CHASE, gs.EATEN) or ghost.target is None:
            continue
        gx, gy = int(ghost.x), int(ghost.y) + MAZE_Y
        tx, ty = _center(ghost.target)
        pygame.draw.line(layer, color + (170,), (gx, gy), (tx, ty), 1)
        pygame.draw.rect(layer, color + (255,), (tx - TILE // 2, ty - TILE // 2, TILE, TILE), 2)

        if ghost.state is gs.CHASE:
            if ghost.name == "pinky":
                pygame.draw.line(layer, color + (120,), pac_center, (tx, ty), 3)
            elif ghost.name == "inky":
                pivot = _center(tiles_ahead(pac.maze_tile, pac.direction, 2))
                blinky = world.by_name["blinky"]
                bx, by = int(blinky.x), int(blinky.y) + MAZE_Y
                pygame.draw.line(layer, (255, 255, 255, 110), (bx, by), pivot, 1)
                pygame.draw.line(layer, color + (110,), pivot, (tx, ty), 1)
                pygame.draw.circle(layer, (255, 255, 255, 200), pivot, 3)
            elif ghost.name == "clyde":
                pygame.draw.circle(layer, color + (90,), (gx, gy), PokeyTargeting.RADIUS * TILE, 1)

    surface.blit(layer, (0, 0))

    modes = world.modes
    if modes.frightened:
        status = f"ASSUSTADAS {modes.fright_left:4.1f}s"
    else:
        left = modes.time_left
        status = f"{MODE_NAMES[modes.mode]} " + ("SEMPRE" if left > 900 else f"{left:4.1f}s")
    draw_text(surface, assets, "RAIO-X: " + status, 8, (255, 255, 255), (4, MAZE_Y + 2), "topleft", shadow=(0, 0, 0))
    elroy = world.elroy_level(world.by_name["blinky"])
    counters = world.house.counters
    info = f"ELROY {elroy}  CASA P{counters['pinky']} I{counters['inky']} C{counters['clyde']}"
    if world.house.use_global:
        info += f" G{world.house.global_counter}"
    draw_text(surface, assets, info, 8, (200, 200, 200), (4, MAZE_Y + 12), "topleft", shadow=(0, 0, 0))
