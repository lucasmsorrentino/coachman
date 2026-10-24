"""Tabela de dificuldade por fase, igual à do arcade.

Fonte: Jamey Pittman, *The Pac-Man Dossier*, tabela "Level Specifications"
(https://www.gamedeveloper.com/design/the-pac-man-dossier).

As velocidades são frações da velocidade máxima (``config.BASE_SPEED``).
Os tempos estão em segundos.

Esta é uma abordagem *data-driven*: a lógica do jogo é a mesma em todas as
fases; o que muda é só este registro de dados (``LevelSpec``).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

INFINITE = math.inf


@dataclass(frozen=True)
class LevelSpec:
    level: int
    bonus_points: int  # pontos da vovó (no arcade: cereja, morango, laranja...)
    pac_speed: float
    pac_fright_speed: float
    ghost_speed: float
    ghost_tunnel_speed: float
    ghost_fright_speed: float
    elroy1_dots: int  # Blinky acelera quando restam <= N bolinhas ("Cruise Elroy")
    elroy1_speed: float
    elroy2_dots: int
    elroy2_speed: float
    fright_time: float  # duração do modo assustado (0 = só inverte a direção)
    fright_flashes: int
    # Alternância dispersão/perseguição: [disp, pers, disp, pers, ...]; a
    # última perseguição é infinita.
    mode_durations: tuple[float, ...]
    # Contadores de bolinhas para liberar cada fantasma da casa
    dot_limits: dict[str, int]
    # Se o jogador ficar este tempo sem comer, o próximo fantasma sai da casa
    house_idle_limit: float


_BONUS = {1: 100, 2: 300, 3: 500, 4: 500, 5: 700, 6: 700, 7: 1000, 8: 1000, 9: 2000, 10: 2000, 11: 3000, 12: 3000}
_FRIGHT = {1: (6, 5), 2: (5, 5), 3: (4, 5), 4: (3, 5), 5: (2, 5), 6: (5, 5), 7: (2, 5), 8: (2, 5), 9: (1, 3),
           10: (5, 5), 11: (2, 5), 12: (1, 3), 13: (1, 3), 14: (3, 5), 15: (1, 3), 16: (1, 3), 17: (0, 0), 18: (1, 3)}
_ELROY_DOTS = {1: 20, 2: 30, 3: 40, 4: 40, 5: 40, 6: 50, 7: 50, 8: 50, 9: 60, 10: 60, 11: 60,
               12: 80, 13: 80, 14: 80, 15: 100, 16: 100, 17: 100, 18: 100}

MODES_L1 = (7, 20, 7, 20, 5, 20, 5, INFINITE)
MODES_L2_4 = (7, 20, 7, 20, 5, 1033, 1 / 60, INFINITE)
MODES_L5 = (5, 20, 5, 20, 5, 1037, 1 / 60, INFINITE)


def level_spec(level: int) -> LevelSpec:
    n = max(1, level)
    if n == 1:
        pac, pac_fright, ghost, tunnel, ghost_fright = 0.80, 0.90, 0.75, 0.40, 0.50
        elroy1, elroy2, modes = 0.80, 0.85, MODES_L1
    elif n <= 4:
        pac, pac_fright, ghost, tunnel, ghost_fright = 0.90, 0.95, 0.85, 0.45, 0.55
        elroy1, elroy2, modes = 0.90, 0.95, MODES_L2_4
    else:
        pac = 1.00 if n <= 20 else 0.90
        pac_fright, ghost, tunnel, ghost_fright = 1.00, 0.95, 0.50, 0.60
        elroy1, elroy2, modes = 1.00, 1.05, MODES_L5
    fright_time, flashes = _FRIGHT.get(n, (0, 0))
    elroy_dots = _ELROY_DOTS.get(n, 120)
    if n == 1:
        limits = {"pinky": 0, "inky": 30, "clyde": 60}
    elif n == 2:
        limits = {"pinky": 0, "inky": 0, "clyde": 50}
    else:
        limits = {"pinky": 0, "inky": 0, "clyde": 0}
    return LevelSpec(
        level=n,
        bonus_points=_BONUS.get(n, 5000),
        pac_speed=pac,
        pac_fright_speed=pac_fright,
        ghost_speed=ghost,
        ghost_tunnel_speed=tunnel,
        ghost_fright_speed=ghost_fright,
        elroy1_dots=elroy_dots,
        elroy1_speed=elroy1,
        elroy2_dots=elroy_dots // 2,
        elroy2_speed=elroy2,
        fright_time=float(fright_time),
        fright_flashes=flashes,
        mode_durations=modes,
        dot_limits=limits,
        house_idle_limit=4.0 if n <= 4 else 3.0,
    )
