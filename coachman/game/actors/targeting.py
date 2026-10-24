"""As "personalidades" das cadeiras voadoras -- padrão **Strategy**
(GoF, "Strategy", p. 315).

No Pac-Man original os quatro fantasmas usam *exatamente o mesmo* algoritmo
de movimento (ver ``ghost_states.choose_toward``); a única diferença entre
eles é **qual tile cada um persegue** no modo perseguição. Essa diferença é
isolada em estratégias intercambiáveis:

=========  ===================  ==========================================
Cadeira    Apelido (arcade)     Alvo no modo perseguição
=========  ===================  ==========================================
Blinky     Shadow / Oikake      o tile do Coach-Man
Pinky      Speedy / Machibuse   4 tiles à frente do Coach-Man
Inky       Bashful / Kimagure   reflexo do Blinky em torno de 2 tiles à frente
Clyde      Pokey / Otoboke      o Coach-Man se estiver a 8+ tiles; senão, o
                                próprio canto de dispersão
=========  ===================  ==========================================

Explicação completa (com diagramas): ``docs/FANTASMAS.md``.
Fontes: Chad Birch, "Understanding Pac-Man Ghost Behavior"
(https://gameinternals.com/understanding-pac-man-ghost-behavior) e
Jamey Pittman, "The Pac-Man Dossier".
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..world.direction import Direction
from ..world.maze import Tile

#: No arcade, "N tiles à frente" quando o Pac-Man olha para CIMA também anda N
#: tiles para a ESQUERDA, por causa de um estouro de 8 bits no cálculo. O jogo
#: reproduz esse bug por fidelidade (mude para False para a versão "corrigida").
REPRODUCE_ARCADE_OVERFLOW_BUG = True


@dataclass(frozen=True)
class TargetContext:
    """Tudo o que uma estratégia pode olhar para escolher o alvo."""

    pac_tile: Tile
    pac_direction: Direction
    ghost_tile: Tile
    blinky_tile: Tile
    scatter_tile: Tile


def tiles_ahead(tile: Tile, direction: Direction, n: int) -> Tile:
    c, r = tile
    c, r = c + direction.dx * n, r + direction.dy * n
    if REPRODUCE_ARCADE_OVERFLOW_BUG and direction is Direction.UP:
        c -= n
    return c, r


class TargetingStrategy(ABC):
    name: str = ""
    nickname: str = ""
    description: str = ""

    @abstractmethod
    def chase_target(self, ctx: TargetContext) -> Tile: ...


class ShadowTargeting(TargetingStrategy):
    """Blinky: persegue direto. É o mais perigoso por trás de você."""

    name, nickname = "BLINKY", "PERSEGUIDORA"
    description = "Mira o tile do Coach-Man."

    def chase_target(self, ctx: TargetContext) -> Tile:
        return ctx.pac_tile


class AmbushTargeting(TargetingStrategy):
    """Pinky: tenta cortar o caminho, mirando 4 tiles à frente."""

    name, nickname = "PINKY", "EMBOSCADA"
    description = "Mira 4 tiles à frente do Coach-Man."

    def chase_target(self, ctx: TargetContext) -> Tile:
        return tiles_ahead(ctx.pac_tile, ctx.pac_direction, 4)


class WhimsicalTargeting(TargetingStrategy):
    """Inky: usa o Blinky como referência -- o vetor Blinky -> (2 à frente do
    Coach-Man) é dobrado. Quando o Blinky está perto, o Inky também cerca;
    quando está longe, o Inky parece andar a esmo."""

    name, nickname = "INKY", "IMPREVISIVEL"
    description = "Dobra o vetor Blinky -> 2 tiles à frente."

    def chase_target(self, ctx: TargetContext) -> Tile:
        pivot_c, pivot_r = tiles_ahead(ctx.pac_tile, ctx.pac_direction, 2)
        bc, br = ctx.blinky_tile
        return 2 * pivot_c - bc, 2 * pivot_r - br


class PokeyTargeting(TargetingStrategy):
    """Clyde: persegue de longe, mas foge para o canto quando chega perto."""

    name, nickname = "CLYDE", "DESLIGADA"
    description = "Longe (>= 8 tiles): persegue. Perto: volta ao canto."
    RADIUS = 8

    def chase_target(self, ctx: TargetContext) -> Tile:
        dc = ctx.ghost_tile[0] - ctx.pac_tile[0]
        dr = ctx.ghost_tile[1] - ctx.pac_tile[1]
        if dc * dc + dr * dr >= self.RADIUS * self.RADIUS:
            return ctx.pac_tile
        return ctx.scatter_tile
