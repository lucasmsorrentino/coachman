"""O Coach-Man (o "Pac-Man" deste jogo).

Comportamentos do arcade reproduzidos aqui:

* **Direção desejada com memória**: a última seta apertada fica guardada e é
  aplicada assim que possível (como manter o joystick inclinado).
* **Meia-volta instantânea**: inverter o sentido vale a qualquer momento.
* **Curva antecipada ("cornering")**: se o jogador pede uma curva *antes* de
  chegar ao centro do cruzamento, o Coach-Man já começa a virar e anda na
  diagonal até se alinhar -- é por isso que no arcade o Pac-Man ganha
  distância dos fantasmas nas curvas. As cadeiras não sabem fazer isso.
* **Pausa ao comer**: 1 quadro parado por "$" e 3 por power-up (feito pelo
  ``World`` via ``freeze``), o que deixa o jogador mais lento em corredores
  cheios e mais rápido nos vazios -- exatamente como no original.
"""
from __future__ import annotations

from ..world.direction import Direction
from ..world.maze import Maze
from .actor import Actor


class CoachMan(Actor):
    ANIM_STEP = 4.0  # pixels andados por quadro de animação
    ANIM_CYCLE = (0, 1, 2, 1)  # aberta, meia, fechada, meia

    def __init__(self, maze: Maze, x: float, y: float) -> None:
        super().__init__(maze, x, y, Direction.LEFT)
        self.wanted: Direction | None = None
        self.speed_factor = 0.8
        self._anim_distance = 0.0

    def reset(self, x: float, y: float) -> None:
        self.place(x, y, Direction.LEFT)
        self.wanted = None
        self.freeze = 0
        self._anim_distance = 0.0

    # ------------------------------------------------------------------ entrada
    def steer(self, direction: Direction) -> None:
        self.wanted = direction

    # ------------------------------------------------------------------ ganchos do Template Method
    def speed(self) -> float:
        return self.speed_factor

    def before_move(self) -> None:
        wanted = self.wanted
        if wanted is None or wanted == self.direction:
            return
        if wanted == self.direction.opposite:
            self.direction = wanted
            return
        c, r = self.tile
        if self.maze.pacman_can_enter(c + wanted.dx, r + wanted.dy):
            self.direction = wanted  # curva antecipada: o resto é feito por _align_cross_axis

    def choose_direction_at_center(self) -> Direction | None:
        c, r = self.tile
        if self.wanted and self.maze.pacman_can_enter(c + self.wanted.dx, r + self.wanted.dy):
            return self.wanted
        if self.maze.pacman_can_enter(c + self.direction.dx, r + self.direction.dy):
            return self.direction
        return None

    def after_move(self) -> None:
        self._anim_distance += self.moved

    # ------------------------------------------------------------------ animação
    @property
    def anim_frame(self) -> int:
        step = int(self._anim_distance // self.ANIM_STEP)
        return self.ANIM_CYCLE[step % len(self.ANIM_CYCLE)]
