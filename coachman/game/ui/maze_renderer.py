"""Desenho das paredes no estilo do arcade (contornos arredondados).

As paredes não são "quadrados azuis": como no Pac-Man, desenhamos só o
*contorno* de cada bloco, passando pelo centro dos tiles de parede que
encostam num corredor. Regras:

* dois tiles de parede vizinhos são ligados por um segmento se, de pelo
  menos um dos lados do segmento, existe corredor;
* um tile com exatamente duas ligações perpendiculares vira uma curva de
  1/4 de círculo (canto arredondado);
* a borda externa (paredes ligadas à borda do mapa) e a casa das cadeiras
  ganham linha dupla, como no original.

O resultado é desenhado uma única vez numa ``Surface`` (cache) e só copiado
para a tela a cada quadro.
"""
from __future__ import annotations

import pygame

from ..config import DOOR_COLOR, TILE
from ..world.direction import Direction
from ..world.maze import Maze, Tile


def _is_solid(maze: Maze, c: int, r: int) -> bool:
    if not 0 <= r < maze.rows or not 0 <= c < maze.cols:
        return True
    return (c, r) in maze.walls


def wall_links(maze: Maze) -> dict[Tile, set[Direction]]:
    """Para cada tile de parede, as direções em que o contorno continua."""
    links: dict[Tile, set[Direction]] = {}
    for c, r in maze.walls:
        dirs = set()
        for d in (Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP):
            nc, nr = c + d.dx, r + d.dy
            if (nc, nr) not in maze.walls:
                continue
            # os dois pares de tiles de cada lado do segmento (c,r)-(nc,nr)
            px, py = (0, 1) if d.is_horizontal else (1, 0)
            side_a = _is_solid(maze, c - px, r - py) and _is_solid(maze, nc - px, nr - py)
            side_b = _is_solid(maze, c + px, r + py) and _is_solid(maze, nc + px, nr + py)
            if not (side_a and side_b):
                dirs.add(d)
        if dirs:
            links[(c, r)] = dirs
    return links


def outer_walls(maze: Maze) -> set[Tile]:
    """Paredes conectadas à borda do mapa (recebem linha dupla)."""
    stack = [(c, r) for (c, r) in maze.walls if c in (0, maze.cols - 1) or r in (0, maze.rows - 1)]
    seen = set(stack)
    while stack:
        c, r = stack.pop()
        for d in Direction:
            n = (c + d.dx, r + d.dy)
            if n in maze.walls and n not in seen:
                seen.add(n)
                stack.append(n)
    return seen


def house_walls(maze: Maze) -> set[Tile]:
    stack = [(c + d.dx, r + d.dy) for (c, r) in maze.doors for d in (Direction.LEFT, Direction.RIGHT)]
    stack = [t for t in stack if t in maze.walls]
    seen = set(stack)
    while stack:
        c, r = stack.pop()
        for d in Direction:
            n = (c + d.dx, r + d.dy)
            if n in maze.walls and n not in seen:
                seen.add(n)
                stack.append(n)
    return seen


_CORNERS = {
    # (direção A, direção B): (deslocamento do centro do arco, quadrante do círculo)
    frozenset((Direction.RIGHT, Direction.DOWN)): ((1, 1), "top_left"),
    frozenset((Direction.LEFT, Direction.DOWN)): ((0, 1), "top_right"),
    frozenset((Direction.RIGHT, Direction.UP)): ((1, 0), "bottom_left"),
    frozenset((Direction.LEFT, Direction.UP)): ((0, 0), "bottom_right"),
}


def _stroke(surface: pygame.Surface, links: dict[Tile, set[Direction]], tiles, color, width: int) -> None:
    """Desenha o contorno dos ``tiles`` com uma linha de espessura ``width``."""
    half = TILE // 2
    lo = width // 2
    for c, r in tiles:
        dirs = links.get((c, r))
        if not dirs:
            continue
        x0, y0 = c * TILE, r * TILE
        cx, cy = x0 + half, y0 + half
        corner = _CORNERS.get(frozenset(dirs)) if len(dirs) == 2 else None
        if corner:
            (ox, oy), quadrant = corner
            center = (x0 + ox * TILE, y0 + oy * TILE)
            pygame.draw.circle(surface, color, center, half + lo, width, **{f"draw_{quadrant}": True})
            continue
        for d in dirs:
            if d is Direction.RIGHT:
                surface.fill(color, (cx - lo, cy - lo, half + lo, width))
            elif d is Direction.LEFT:
                surface.fill(color, (x0, cy - lo, half + width - lo, width))
            elif d is Direction.DOWN:
                surface.fill(color, (cx - lo, cy - lo, width, half + lo))
            elif d is Direction.UP:
                surface.fill(color, (cx - lo, y0, width, half + width - lo))


def render_walls(maze: Maze, color: tuple[int, int, int], size: tuple[int, int]) -> pygame.Surface:
    surface = pygame.Surface(size, pygame.SRCALPHA)
    links = wall_links(maze)
    double = outer_walls(maze) | house_walls(maze)
    single = set(links) - double
    # porta da casa (rosa) entre as paredes da casa
    for c, r in maze.doors:
        surface.fill(DOOR_COLOR, (c * TILE, r * TILE + TILE // 2 - 2, TILE, 4))
    # linha dupla: traço grosso colorido + traço fino "apagando" o meio
    _stroke(surface, links, double, color, 6)
    _stroke(surface, links, double, (0, 0, 0, 0), 2)
    _stroke(surface, links, single, color, 2)
    return surface
