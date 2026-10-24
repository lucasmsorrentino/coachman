"""Comportamento das cadeiras voadoras -- padrão **State** (GoF, p. 305).

Uma cadeira (o *Context*, ``Ghost``) delega velocidade, escolha de direção e
movimento ao seu estado atual. Trocar de comportamento = trocar de objeto
estado; não existe um ``if modo == ...`` espalhado pelo código.

Diagrama (também em ``docs/FANTASMAS.md``)::

    NA CASA --liberada--> SAINDO --> DISPERSÃO <--timer--> PERSEGUIÇÃO
                                         \\                   /
                                       power-up          power-up
                                           v                v
                                            ASSUSTADA (azul)
                                                 | comida pelo Coach-Man
                                                 v
                                     DEVORADA ("espírito") --> ENTRANDO --> SAINDO

Os estados não guardam dados próprios (tudo fica na cadeira), então uma única
instância de cada estado é compartilhada pelas quatro cadeiras -- exatamente
a variação "objetos State compartilhados" descrita no livro do GoF.
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..config import BASE_SPEED
from ..world.direction import PRIORITY, Direction
from ..world.maze import Tile

if TYPE_CHECKING:  # pragma: no cover
    from .ghost import Ghost

HOUSE_SPEED = 0.5
EYES_SPEED = 1.7


# --------------------------------------------------------------------------
# O algoritmo de navegação do arcade (comum a todas as cadeiras)
# --------------------------------------------------------------------------
def choose_toward(ghost: "Ghost", target: Tile, restrict_up: bool = True) -> Direction:
    """Escolhe a saída do tile atual que deixa a cadeira mais perto do alvo.

    Regras do arcade:
    1. nunca dar meia-volta por conta própria;
    2. nunca entrar em parede (nem na porta da casa);
    3. nos tiles "proibido subir" do labirinto, não vira para cima;
    4. entre as saídas restantes, vence a de menor distância em linha reta
       (euclidiana) entre o *tile vizinho* e o alvo -- não é busca de caminho!
    5. empate: prioridade cima > esquerda > baixo > direita.
    """
    c, r = ghost.tile
    tc, tr = target
    best, best_dist = None, math.inf
    for d in PRIORITY:
        if d is ghost.direction.opposite:
            continue
        if restrict_up and d is Direction.UP and ghost.maze_tile in ghost.maze.definition.no_up_tiles:
            continue
        nc, nr = c + d.dx, r + d.dy
        if not ghost.maze.ghost_can_enter(nc, nr):
            continue
        dist = (nc - tc) ** 2 + (nr - tr) ** 2  # sem raiz: a ordem é a mesma
        if dist < best_dist:
            best, best_dist = d, dist
    return best or ghost.direction.opposite  # beco sem saída (não existe nos mapas)


def choose_random(ghost: "Ghost") -> Direction:
    """Modo assustado: direção pseudoaleatória em cada cruzamento.

    Como no arcade, sorteia uma direção; se ela for inválida, tenta as
    seguintes na ordem cima, esquerda, baixo, direita.
    """
    c, r = ghost.tile
    start = ghost.world.rng.randrange(4)
    for i in range(4):
        d = PRIORITY[(start + i) % 4]
        if d is not ghost.direction.opposite and ghost.maze.ghost_can_enter(c + d.dx, r + d.dy):
            return d
    return ghost.direction.opposite


# --------------------------------------------------------------------------
# Estados
# --------------------------------------------------------------------------
class GhostState(ABC):
    name = ""
    deadly = False  # encostar no Coach-Man o mata
    edible = False  # encostar no Coach-Man faz a cadeira ser comida

    def enter(self, ghost: "Ghost") -> None: ...

    def update(self, ghost: "Ghost") -> None:
        ghost.move_in_maze()  # Template Method do Actor (anda de centro em centro)

    @abstractmethod
    def speed(self, ghost: "Ghost") -> float: ...

    def choose_direction(self, ghost: "Ghost") -> Direction | None:
        return ghost.direction

    def __repr__(self) -> str:
        return self.name


class ScatterState(GhostState):
    """Dispersão: cada cadeira volta para o seu canto e fica rodando nele."""

    name = "DISPERSAO"
    deadly = True

    def speed(self, ghost: "Ghost") -> float:
        return ghost.world.ghost_speed(ghost)

    def target(self, ghost: "Ghost") -> Tile:
        # "Cruise Elroy": o Blinky acelerado ignora a dispersão e persegue.
        if ghost.world.elroy_level(ghost) > 0:
            return ghost.world.target_context(ghost).pac_tile
        return ghost.scatter_tile

    def choose_direction(self, ghost: "Ghost") -> Direction:
        ghost.target = self.target(ghost)
        return choose_toward(ghost, ghost.target)


class ChaseState(ScatterState):
    """Perseguição: o alvo vem da *estratégia* (personalidade) da cadeira."""

    name = "PERSEGUICAO"

    def target(self, ghost: "Ghost") -> Tile:
        return ghost.strategy.chase_target(ghost.world.target_context(ghost))


class FrightenedState(GhostState):
    name = "ASSUSTADA"
    edible = True

    def speed(self, ghost: "Ghost") -> float:
        spec = ghost.world.spec
        if ghost.maze.is_tunnel(*ghost.maze_tile):
            return min(spec.ghost_fright_speed, spec.ghost_tunnel_speed)
        return spec.ghost_fright_speed

    def choose_direction(self, ghost: "Ghost") -> Direction:
        ghost.target = None
        return choose_random(ghost)


class EatenState(GhostState):
    """Só o "espírito" da cadeira volta voando para a casa."""

    name = "DEVORADA"

    def speed(self, ghost: "Ghost") -> float:
        return EYES_SPEED

    def choose_direction(self, ghost: "Ghost") -> Direction | None:
        if ghost.maze_tile in ghost.maze.house_exit_tiles:
            ghost.change_state(ENTERING_HOUSE)
            return None  # para aqui; o estado ENTRANDO assume no próximo quadro
        ghost.target = min(ghost.maze.house_exit_tiles)
        return choose_toward(ghost, ghost.target, restrict_up=False)


class _HouseMovement(GhostState):
    """Movimento livre (fora da grade) dentro e na porta da casa."""

    def step_towards(self, ghost: "Ghost", x: float, y: float, speed: float) -> bool:
        budget = speed * BASE_SPEED
        dx, dy = x - ghost.x, y - ghost.y
        if abs(dx) > 1e-6:
            move = max(-budget, min(budget, dx))
            ghost.x += move
            ghost.direction = Direction.RIGHT if dx > 0 else Direction.LEFT
            return False
        if abs(dy) > 1e-6:
            move = max(-budget, min(budget, dy))
            ghost.y += move
            ghost.direction = Direction.DOWN if dy > 0 else Direction.UP
            return False
        return True


class InHouseState(_HouseMovement):
    """Esperando a vez: sobe e desce dentro da casa."""

    name = "NA CASA"

    def speed(self, ghost: "Ghost") -> float:
        return HOUSE_SPEED

    def update(self, ghost: "Ghost") -> None:
        if ghost.freeze > 0:
            ghost.freeze -= 1
            return
        center = ghost.maze.house_inside_y
        going_up = ghost.direction is Direction.UP
        goal = center - 4 if going_up else center + 4
        if self.step_towards(ghost, ghost.home_x, goal, HOUSE_SPEED):
            ghost.direction = Direction.DOWN if going_up else Direction.UP


class LeavingHouseState(_HouseMovement):
    name = "SAINDO"

    def speed(self, ghost: "Ghost") -> float:
        return HOUSE_SPEED

    def update(self, ghost: "Ghost") -> None:
        if ghost.freeze > 0:
            ghost.freeze -= 1
            return
        maze = ghost.maze
        if abs(ghost.x - maze.house_center_x) > 1e-6:
            # primeiro alinha com a porta (no centro vertical da casa)
            if abs(ghost.y - maze.house_inside_y) > 1e-6:
                self.step_towards(ghost, ghost.x, maze.house_inside_y, HOUSE_SPEED)
            else:
                self.step_towards(ghost, maze.house_center_x, ghost.y, HOUSE_SPEED)
            return
        if self.step_towards(ghost, maze.house_center_x, maze.house_exit_y, HOUSE_SPEED):
            # saiu: vai para a esquerda (ou direita, se o modo mudou enquanto
            # estava na casa) e assume o modo global.
            ghost.direction = Direction.RIGHT if ghost.exit_right else Direction.LEFT
            ghost.exit_right = False
            ghost.change_state(FRIGHTENED if ghost.frightened else ghost.world.global_mode_state())


class EnteringHouseState(_HouseMovement):
    name = "ENTRANDO"

    def speed(self, ghost: "Ghost") -> float:
        return EYES_SPEED

    def update(self, ghost: "Ghost") -> None:
        maze = ghost.maze
        if abs(ghost.y - maze.house_exit_y) < 1e-6 and abs(ghost.x - maze.house_center_x) > 1e-6:
            self.step_towards(ghost, maze.house_center_x, ghost.y, EYES_SPEED)
        elif self.step_towards(ghost, maze.house_center_x, maze.house_inside_y, EYES_SPEED):
            ghost.revive()


SCATTER = ScatterState()
CHASE = ChaseState()
FRIGHTENED = FrightenedState()
EATEN = EatenState()
IN_HOUSE = InHouseState()
LEAVING_HOUSE = LeavingHouseState()
ENTERING_HOUSE = EnteringHouseState()
