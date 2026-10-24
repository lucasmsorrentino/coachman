"""Uma fase em andamento: labirinto + Coach-Man + cadeiras + sistemas.

O ``World`` coordena a simulação quadro a quadro (é o *Mediator* entre as
entidades: elas não se conhecem diretamente) e publica no ``EventBus`` tudo o
que acontece. Ele não sabe nada de placar, som ou desenho.
"""
from __future__ import annotations

import random

from ..actors import ghost_states as gs
from ..actors.factory import EntityFactory
from ..actors.ghost import Ghost
from ..actors.targeting import TargetContext
from ..config import BONUS_DOTS, DOT_PAUSE, ENERGIZER_PAUSE, GHOST_EAT_PAUSE, GHOST_POINTS, TILE
from ..core.events import (
    BonusEaten,
    BonusSpawned,
    CoachManCaught,
    DotEaten,
    EnergizerEaten,
    EventBus,
    FrightEnded,
    FrightStarted,
    GhostEaten,
    LevelCleared,
    ModeChanged,
)
from ..levels import level_spec
from ..systems.ghost_house import GhostHouse
from ..systems.mode_scheduler import CHASE, ModeScheduler
from .maze import Maze, MazeDefinition
from .maze_data import maze_for_level

POWERUP_ICONS = 7  # X, Instagram, TikTok, YouTube, Facebook, Discord, WhatsApp


class Bonus:
    """A vovó: a "frutinha" que aparece duas vezes por fase."""

    def __init__(self, x: float, y: float) -> None:
        self.x, self.y = x, y
        self.time_left = 0.0

    @property
    def active(self) -> bool:
        return self.time_left > 0

    def spawn(self, seconds: float) -> None:
        self.time_left = seconds

    def hide(self) -> None:
        self.time_left = 0.0

    def update(self, dt: float) -> None:
        self.time_left = max(0.0, self.time_left - dt)


class World:
    def __init__(
        self,
        level: int,
        bus: EventBus,
        rng: random.Random | None = None,
        definition: MazeDefinition | None = None,
    ) -> None:
        self.level = level
        self.bus = bus
        self.rng = rng or random.Random()
        self.spec = level_spec(level)
        self.maze = Maze.from_definition(definition or maze_for_level(level))
        # Power-ups com logos sorteados (4 dos 7) a cada fase
        icons = self.rng.sample(range(POWERUP_ICONS), len(self.maze.energizers))
        for tile, icon in zip(sorted(self.maze.energizers), icons):
            self.maze.energizers[tile] = icon

        factory = EntityFactory(self.maze)
        self.coachman = factory.create_coachman()
        self.ghosts: list[Ghost] = factory.create_ghosts(self)
        self.by_name = {g.name: g for g in self.ghosts}
        self.modes = ModeScheduler(self.spec.mode_durations)
        self.house = GhostHouse(self.spec, self.ghosts)
        bx, by = self.maze.definition.bonus_position
        self.bonus = Bonus(bx * TILE, by * TILE)
        self.bonus_thresholds_hit: set[int] = set()

        self.ghost_combo = 0  # cadeiras comidas com o power-up atual
        self.elroy_suspended = False
        self.pause_frames = 0  # congelamento global (ao comer uma cadeira)
        self.eaten_ghost: tuple[Ghost, int] | None = None  # (cadeira, pontos) durante a pausa
        self.caught_by: Ghost | None = None
        self.cleared = False
        self.frame = 0

    # ------------------------------------------------------------------ GhostWorld (o que as cadeiras consultam)
    def target_context(self, ghost: Ghost) -> TargetContext:
        return TargetContext(
            pac_tile=self.coachman.maze_tile,
            pac_direction=self.coachman.direction,
            ghost_tile=ghost.tile,
            blinky_tile=self.by_name["blinky"].tile,
            scatter_tile=ghost.scatter_tile,
        )

    def global_mode_state(self) -> gs.GhostState:
        return gs.CHASE if self.modes.mode == CHASE else gs.SCATTER

    def elroy_level(self, ghost: Ghost) -> int:
        if ghost.name != "blinky" or self.elroy_suspended:
            return 0
        left = self.maze.food_left
        if left <= self.spec.elroy2_dots:
            return 2
        if left <= self.spec.elroy1_dots:
            return 1
        return 0

    def ghost_speed(self, ghost: Ghost) -> float:
        spec = self.spec
        if self.maze.is_tunnel(*ghost.maze_tile):
            return spec.ghost_tunnel_speed
        elroy = self.elroy_level(ghost)
        if elroy == 2:
            return spec.elroy2_speed
        if elroy == 1:
            return spec.elroy1_speed
        return spec.ghost_speed

    # ------------------------------------------------------------------ simulação
    def update(self, dt: float) -> None:
        self.frame += 1
        if self.pause_frames > 0:
            self.pause_frames -= 1
            if self.pause_frames == 0:
                self.eaten_ghost = None
            return

        for event in self.modes.update(dt):
            if event == "mode":
                self._on_mode_change()
            elif event == "fright_end":
                self._end_fright()
        self.house.update(dt)
        if self.elroy_suspended and not self.by_name["clyde"].in_house:
            self.elroy_suspended = False

        pac = self.coachman
        pac.speed_factor = self.spec.pac_fright_speed if self.modes.frightened else self.spec.pac_speed
        pac.update()
        self._eat(pac.maze_tile)
        if self._check_collisions():
            return
        for ghost in self.ghosts:
            ghost.update()
        if self._check_collisions():
            return

        self._update_bonus(dt)
        if self.maze.food_left == 0 and not self.cleared:
            self.cleared = True
            self.bus.publish(LevelCleared(self.level))

    # ------------------------------------------------------------------ comida
    def _eat(self, tile) -> None:
        kind = self.maze.eat(tile)
        if kind is None:
            return
        self.house.on_dot_eaten()
        if kind == "dot":
            self.coachman.freeze = DOT_PAUSE
            self.bus.publish(DotEaten(tile, self.maze.food_left))
        else:
            self.coachman.freeze = ENERGIZER_PAUSE
            self.bus.publish(EnergizerEaten(tile, self.maze.food_left))
            self._start_fright()
        eaten = self.maze.food_eaten
        if eaten in BONUS_DOTS and eaten not in self.bonus_thresholds_hit:
            self.bonus_thresholds_hit.add(eaten)
            self.bonus.spawn(self.rng.uniform(9.0, 10.0))
            self.bus.publish(BonusSpawned((self.bonus.x, self.bonus.y)))

    def _update_bonus(self, dt: float) -> None:
        if not self.bonus.active:
            return
        self.bonus.update(dt)
        pac = self.coachman
        if abs(pac.x - self.bonus.x) < TILE and pac.tile[1] == int(self.bonus.y // TILE):
            self.bonus.hide()
            self.bus.publish(BonusEaten(self.spec.bonus_points, (self.bonus.x, self.bonus.y)))

    # ------------------------------------------------------------------ modos
    def _on_mode_change(self) -> None:
        state = self.global_mode_state()
        for ghost in self.ghosts:
            if ghost.roaming:
                ghost.change_state(state)
                ghost.reverse()  # toda troca de modo faz as cadeiras darem meia-volta
            elif ghost.in_house:
                ghost.exit_right = True
        self.bus.publish(ModeChanged(self.modes.mode))

    def _start_fright(self) -> None:
        self.ghost_combo = 0
        seconds = self.spec.fright_time
        if seconds > 0:
            self.modes.start_fright(seconds, self.spec.fright_flashes)
        for ghost in self.ghosts:
            if ghost.state in (gs.EATEN, gs.ENTERING_HOUSE):
                continue
            if ghost.roaming or ghost.state is gs.FRIGHTENED:
                ghost.reverse()
            if seconds > 0:
                ghost.frightened = True
                if ghost.roaming:
                    ghost.change_state(gs.FRIGHTENED)
        if seconds > 0:
            self.bus.publish(FrightStarted(seconds))

    def _end_fright(self) -> None:
        for ghost in self.ghosts:
            ghost.frightened = False
            if ghost.state is gs.FRIGHTENED:
                ghost.change_state(self.global_mode_state())
        self.bus.publish(FrightEnded())

    # ------------------------------------------------------------------ colisões
    @staticmethod
    def is_edible(ghost: Ghost) -> bool:
        return ghost.state is gs.FRIGHTENED or (ghost.state is gs.LEAVING_HOUSE and ghost.frightened)

    @staticmethod
    def is_deadly(ghost: Ghost) -> bool:
        return ghost.roaming or (ghost.state is gs.LEAVING_HOUSE and not ghost.frightened)

    def _check_collisions(self) -> bool:
        """Mesmo tile = encostou (regra do arcade). Devolve True se algo aconteceu."""
        pac_tile = self.coachman.maze_tile
        for ghost in self.ghosts:
            if ghost.maze_tile != pac_tile:
                continue
            if self.is_edible(ghost):
                points = GHOST_POINTS[min(self.ghost_combo, len(GHOST_POINTS) - 1)]
                self.ghost_combo += 1
                ghost.frightened = False
                ghost.change_state(gs.EATEN)
                self.pause_frames = GHOST_EAT_PAUSE
                self.eaten_ghost = (ghost, points)
                self.bus.publish(GhostEaten(ghost.name, points, (ghost.x, ghost.y)))
                return True
            if self.is_deadly(ghost):
                self.caught_by = ghost
                self.bus.publish(CoachManCaught(ghost.name))
                return True
        return False

    # ------------------------------------------------------------------ reinício
    def restart_after_death(self) -> None:
        """Volta todos às posições iniciais; as bolinhas comidas continuam comidas."""
        x, y = self.maze.definition.pacman_start
        self.coachman.reset(x * TILE, y * TILE)
        for ghost in self.ghosts:
            ghost.reset()
        self.modes = ModeScheduler(self.spec.mode_durations)
        self.house.on_life_lost()
        self.elroy_suspended = True
        self.bonus.hide()
        self.pause_frames = 0
        self.eaten_ghost = None
        self.caught_by = None
