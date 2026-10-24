"""Modelo do labirinto: paredes, bolinhas, túneis e a casa dos fantasmas.

O labirinto é descrito em texto (ver ``maze_data.py``), um caractere por tile:

====  =====================================================
``#``  parede
``.``  bolinha (10 pontos)
``o``  energizador / power-up (50 pontos, assusta as cadeiras)
`` ``  caminho vazio
``-``  porta da casa dos fantasmas (só fantasmas atravessam)
====  =====================================================

Coordenadas: ``(col, row)`` em tiles, origem no canto superior esquerdo do
labirinto. Posições contínuas das entidades são em pixels (float).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..config import TILE
from .direction import Direction

Tile = tuple[int, int]

WALL, DOT, ENERGIZER, PATH, DOOR = "#", ".", "o", " ", "-"
VALID_CHARS = {WALL, DOT, ENERGIZER, PATH, DOOR}


@dataclass(frozen=True)
class MazeDefinition:
    """Dados declarativos de um labirinto (o "nível" em si)."""

    name: str
    subtitle: str
    layout: tuple[str, ...]
    wall_color: tuple[int, int, int]
    # Tiles onde os fantasmas não podem virar para cima em dispersão/perseguição
    # (no arcade: os dois cruzamentos acima da casa e os dois acima do início).
    no_up_tiles: tuple[Tile, ...] = ()
    # Posições iniciais em unidades de tile (x = 14.0 fica entre as colunas 13 e 14)
    pacman_start: tuple[float, float] = (14.0, 23.5)
    bonus_position: tuple[float, float] = (14.0, 17.5)


@dataclass
class Maze:
    definition: MazeDefinition
    cols: int
    rows: int
    walls: set[Tile]
    doors: set[Tile]
    dots: set[Tile]
    energizers: dict[Tile, int]  # tile -> índice do ícone (X, Instagram, TikTok, YouTube)
    tunnel_tiles: set[Tile] = field(default_factory=set)
    total_food: int = 0

    # ------------------------------------------------------------------ fábrica
    @classmethod
    def from_definition(cls, definition: MazeDefinition) -> "Maze":
        layout = definition.layout
        rows, cols = len(layout), len(layout[0])
        walls, doors, dots = set(), set(), set()
        energizer_tiles = []
        for r, line in enumerate(layout):
            if len(line) != cols:
                raise ValueError(f"{definition.name}: linha {r} tem {len(line)} colunas (esperado {cols})")
            for c, ch in enumerate(line):
                if ch not in VALID_CHARS:
                    raise ValueError(f"{definition.name}: caractere inválido {ch!r} em {(c, r)}")
                if ch == WALL:
                    walls.add((c, r))
                elif ch == DOOR:
                    doors.add((c, r))
                elif ch == DOT:
                    dots.add((c, r))
                elif ch == ENERGIZER:
                    energizer_tiles.append((c, r))
        energizers = {t: i % 4 for i, t in enumerate(sorted(energizer_tiles, key=lambda t: (t[1], t[0])))}
        maze = cls(definition, cols, rows, walls, doors, dots, energizers)
        maze.tunnel_tiles = maze._find_tunnels()
        maze.total_food = len(dots) + len(energizers)
        return maze

    def _find_tunnels(self) -> set[Tile]:
        """Túnel = trecho de corredor que encosta na borda, entre paredes.

        Os fantasmas andam mais devagar nesses tiles (regra do arcade).
        """
        tunnels: set[Tile] = set()
        for r in range(self.rows):
            if self.is_wall(0, r) or self.is_wall(self.cols - 1, r):
                continue
            for start, step in ((0, 1), (self.cols - 1, -1)):
                c = start
                while 0 <= c < self.cols and not self.is_wall(c, r) and self.is_wall(c, r - 1) and self.is_wall(c, r + 1):
                    tunnels.add((c, r))
                    c += step
        return tunnels

    # ------------------------------------------------------------------ consultas
    def wrap_col(self, col: int) -> int:
        return col % self.cols

    def is_wall(self, col: int, row: int) -> bool:
        if not 0 <= row < self.rows:
            return True
        return (self.wrap_col(col), row) in self.walls

    def is_door(self, col: int, row: int) -> bool:
        return (self.wrap_col(col), row) in self.doors

    def is_tunnel(self, col: int, row: int) -> bool:
        return (self.wrap_col(col), row) in self.tunnel_tiles

    def pacman_can_enter(self, col: int, row: int) -> bool:
        return not self.is_wall(col, row) and not self.is_door(col, row)

    def ghost_can_enter(self, col: int, row: int) -> bool:
        """Fantasmas fora de casa não atravessam a porta (só ao sair/entrar)."""
        return self.pacman_can_enter(col, row)

    def exits(self, tile: Tile) -> list[Direction]:
        c, r = tile
        return [d for d in Direction if self.pacman_can_enter(c + d.dx, r + d.dy)]

    # ------------------------------------------------------------------ comida
    def eat(self, tile: Tile) -> str | None:
        """Remove a comida do tile; devolve ``"dot"``, ``"energizer"`` ou None."""
        tile = (self.wrap_col(tile[0]), tile[1])
        if tile in self.dots:
            self.dots.discard(tile)
            return "dot"
        if tile in self.energizers:
            del self.energizers[tile]
            return "energizer"
        return None

    @property
    def food_left(self) -> int:
        return len(self.dots) + len(self.energizers)

    @property
    def food_eaten(self) -> int:
        return self.total_food - self.food_left

    # ------------------------------------------------------------------ casa dos fantasmas
    @property
    def door_row(self) -> int:
        return min(r for _, r in self.doors)

    @property
    def house_center_x(self) -> float:
        """Centro horizontal da porta, em pixels."""
        cols = sorted(c for c, _ in self.doors)
        return (cols[0] + cols[-1] + 1) / 2 * TILE

    @property
    def house_exit_y(self) -> float:
        """Linha logo acima da porta (onde o Blinky começa), em pixels."""
        return (self.door_row - 1 + 0.5) * TILE

    @property
    def house_inside_y(self) -> float:
        return (self.door_row + 2.5) * TILE

    @property
    def house_exit_tiles(self) -> set[Tile]:
        """Tiles acima da porta: destino dos "espíritos" das cadeiras devoradas."""
        return {(c, self.door_row - 1) for c, _ in self.doors}

    def house_slot_x(self, slot: int) -> float:
        """x (px) das vagas na casa: -1 = esquerda, 0 = centro, 1 = direita."""
        return self.house_center_x + slot * 2 * TILE


def tile_of(x: float, y: float) -> Tile:
    """Tile que contém o ponto (x, y) em pixels (sem aplicar o wrap do túnel)."""
    return int(x // TILE), int(y // TILE)


def tile_center(tile: Tile) -> tuple[float, float]:
    return (tile[0] + 0.5) * TILE, (tile[1] + 0.5) * TILE


def validate(definition: MazeDefinition) -> list[str]:
    """Regras de bom labirinto estilo Pac-Man (usadas nos testes).

    * mesmas dimensões do arcade (28 x 31) e simetria horizontal;
    * exatamente 4 energizadores e uma casa com porta;
    * todo caminho alcançável a partir do início do Coach-Man;
    * sem becos sem saída e sem áreas abertas 2 x 2 (corredores de 1 tile);
    * sem blocos de parede isolados de 2 x 2 (seriam desenhados como anéis,
      parecidos demais com itens).
    """
    problems: list[str] = []
    try:
        maze = Maze.from_definition(definition)
    except ValueError as exc:
        return [str(exc)]
    if (maze.cols, maze.rows) != (28, 31):
        problems.append(f"dimensões {maze.cols}x{maze.rows} (esperado 28x31)")
    for r, line in enumerate(definition.layout):
        if line != line[::-1]:
            problems.append(f"linha {r} não é simétrica")
    if len(maze.energizers) != 4:
        problems.append(f"{len(maze.energizers)} energizadores (esperado 4)")
    if not maze.doors:
        problems.append("sem porta da casa dos fantasmas")
        return problems

    walkable = {
        (c, r) for r in range(maze.rows) for c in range(maze.cols) if maze.pacman_can_enter(c, r)
    }
    start = tile_of(definition.pacman_start[0] * TILE, definition.pacman_start[1] * TILE)
    seen, stack = {start}, [start]
    while stack:
        c, r = stack.pop()
        for d in Direction:
            n = (maze.wrap_col(c + d.dx), r + d.dy)
            if n in walkable and n not in seen:
                seen.add(n)
                stack.append(n)
    house_inside = {(c, r) for c, r in walkable if r in range(maze.door_row + 1, maze.door_row + 4)
                    and abs((c + 0.5) * TILE - maze.house_center_x) < 3 * TILE}
    unreachable = walkable - seen - house_inside
    if unreachable:
        problems.append(f"tiles inalcançáveis: {sorted(unreachable)[:6]}")
    for t in seen:
        if len(maze.exits(t)) < 2:
            problems.append(f"beco sem saída em {t}")
    for c in range(maze.cols - 1):
        for r in range(maze.rows - 1):
            block = {(c, r), (c + 1, r), (c, r + 1), (c + 1, r + 1)}
            if block <= seen:
                problems.append(f"área aberta 2x2 em {(c, r)}")
    for comp in _wall_components(maze):
        cols = {c for c, _ in comp}
        rows = {r for _, r in comp}
        if len(comp) == 4 and len(cols) == 2 and len(rows) == 2:
            problems.append(f"bloco de parede 2x2 em {min(comp)}")
    return problems


def _wall_components(maze: Maze) -> list[set[Tile]]:
    """Blocos de parede que não encostam na borda do mapa."""
    seen: set[Tile] = set()
    comps = []
    for start in maze.walls:
        if start in seen:
            continue
        comp, stack = {start}, [start]
        seen.add(start)
        while stack:
            c, r = stack.pop()
            for d in Direction:
                n = (c + d.dx, r + d.dy)
                if n in maze.walls and n not in seen:
                    seen.add(n)
                    comp.add(n)
                    stack.append(n)
        if not any(c in (0, maze.cols - 1) or r in (0, maze.rows - 1) for c, r in comp):
            comps.append(comp)
    return comps
