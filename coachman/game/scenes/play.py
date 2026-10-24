"""A tela de jogo.

Fases de uma rodada (máquina de estados finita simples, com enum):

    INTRO -> READY -> PLAYING -> DYING   -> READY (se ainda há vidas) | GAME_OVER
                              -> CLEARED -> INTRO (próxima fase, próximo labirinto)

A simulação em si fica no ``World``; aqui ficam o ritmo da rodada, o
desenho e as reações visuais/sonoras aos eventos (assinantes do EventBus).
"""
from __future__ import annotations

import math
import random
from enum import Enum, auto

import pygame

from ..actors import ghost_states as gs
from ..actors.ghost import Ghost
from ..config import (
    CYAN,
    MAZE_Y,
    PAUSE_BUTTON,
    RED,
    SCREEN_H,
    SCREEN_W,
    SPRITE,
    TILE,
    WHITE,
    YELLOW,
)
from ..core.audio import AudioService
from ..core.events import (
    BonusEaten,
    DotEaten,
    EnergizerEaten,
    EventBus,
    ExtraLife,
    GhostEaten,
)
from ..core.scenes import Scene
from ..systems.session import Session
from ..ui.debug_overlay import GHOST_COLORS, draw_debug
from ..ui.maze_renderer import render_walls
from ..ui.text import draw_text
from ..world.direction import Direction
from ..world.world import World

DOLLAR_SIZE = (5, 7)
HOVER_PHASE = {"blinky": 0, "pinky": 9, "inky": 18, "clyde": 27}


class Phase(Enum):
    INTRO = auto()
    READY = auto()
    PLAYING = auto()
    DYING = auto()
    CLEARED = auto()
    GAME_OVER = auto()


class SoundEffects:
    """Observer: transforma eventos do jogo em efeitos sonoros."""

    def __init__(self, bus: EventBus, audio: AudioService) -> None:
        self.audio = audio
        self._toggle = False
        bus.subscribe(DotEaten, self._dot)
        bus.subscribe(EnergizerEaten, lambda e: audio.play_sfx("power"))
        bus.subscribe(GhostEaten, lambda e: audio.play_sfx("eat_ghost"))
        bus.subscribe(BonusEaten, lambda e: audio.play_sfx("bonus"))
        bus.subscribe(ExtraLife, lambda e: audio.play_sfx("extra_life"))

    def _dot(self, _event: DotEaten) -> None:
        self._toggle = not self._toggle
        self.audio.play_sfx("dot" if self._toggle else "dot2")


class Popups:
    """Observer: pontos flutuantes (vovó comida)."""

    def __init__(self, bus: EventBus) -> None:
        self.items: list[list] = []  # [texto, x, y, segundos]
        bus.subscribe(BonusEaten, lambda e: self.items.append([str(e.points), e.position[0], e.position[1], 2.0]))

    def update(self, dt: float) -> None:
        for item in self.items:
            item[3] -= dt
        self.items = [i for i in self.items if i[3] > 0]

    def clear(self) -> None:
        self.items.clear()


class PlayScene(Scene):
    music = "gameplay"

    INTRO = 2.6
    READY = 2.0
    DEATH_FREEZE = 1.0
    DEATH_ANIM = 1.6
    CLEAR_FREEZE = 1.0
    CLEAR_FLASH = 2.0
    GAME_OVER_TIME = 2.5

    def __init__(self, app, start_level: int = 1, seed: int | None = None) -> None:
        super().__init__(app)
        self.rng = random.Random(seed)
        self.bus = EventBus()
        self.session = Session(self.bus, high_score=app.scores.best())
        self.sfx = SoundEffects(self.bus, app.audio)
        self.popups = Popups(self.bus)
        self.bus.subscribe(DotEaten, self._erase_dot)
        self.debug = False
        self.frame = 0
        self._start_level(start_level)

    # ------------------------------------------------------------------ fases
    def _start_level(self, level: int) -> None:
        self.session.level = level
        self.world = World(level, self.bus, self.rng)
        definition = self.world.maze.definition
        size = (SCREEN_W, self.world.maze.rows * TILE)
        self.walls = render_walls(self.world.maze, definition.wall_color, size)
        self.walls_flash = render_walls(self.world.maze, WHITE, size)
        self.food_layer = self._render_food(size)
        self.popups.clear()
        self.thumbnail = self._minimap(self.world.maze)
        self._set_phase(Phase.INTRO, self.INTRO)

    def _set_phase(self, phase: Phase, duration: float = 0.0) -> None:
        self.phase = phase
        self.timer = duration
        self.elapsed = 0.0

    def update(self, dt: float) -> None:
        self.frame += 1
        self.timer -= dt
        self.elapsed += dt
        self.popups.update(dt)
        if self.phase is Phase.INTRO:
            if self.timer <= 0:
                self._set_phase(Phase.READY, self.READY)
        elif self.phase is Phase.READY:
            if self.timer <= 0:
                self._set_phase(Phase.PLAYING)
        elif self.phase is Phase.PLAYING:
            self.world.update(dt)
            if self.world.caught_by is not None:
                self.app.audio.stop_music()
                self._set_phase(Phase.DYING, self.DEATH_FREEZE + self.DEATH_ANIM)
            elif self.world.cleared:
                self._set_phase(Phase.CLEARED, self.CLEAR_FREEZE + self.CLEAR_FLASH)
        elif self.phase is Phase.DYING:
            if self.elapsed >= self.DEATH_FREEZE and self.elapsed - dt < self.DEATH_FREEZE:
                self.app.audio.play_sfx("death")
            if self.timer <= 0:
                if self.session.lose_life():
                    self.world.restart_after_death()
                    self.app.audio.play_music("gameplay")
                    self._set_phase(Phase.READY, self.READY)
                else:
                    self._set_phase(Phase.GAME_OVER, self.GAME_OVER_TIME)
        elif self.phase is Phase.CLEARED:
            if self.timer <= 0:
                self._start_level(self.session.level + 1)
        elif self.phase is Phase.GAME_OVER:
            if self.timer <= 0:
                from .gameover import GameOverScene

                self.app.scenes.replace(GameOverScene(self.app, self.session.score, self.session.level))

    # ------------------------------------------------------------------ comandos
    def on_direction(self, direction: Direction) -> None:
        self.world.coachman.steer(direction)

    def on_confirm(self) -> None:
        if self.phase is Phase.INTRO and self.elapsed > 0.4:
            self._set_phase(Phase.READY, self.READY)

    def on_pause(self) -> None:
        if self.phase is not Phase.GAME_OVER:
            from .pause import PauseScene

            self.app.scenes.push(PauseScene(self.app))

    on_back = on_pause

    def on_focus_lost(self) -> None:
        self.on_pause()

    def on_toggle_debug(self) -> None:
        self.debug = not self.debug

    # ------------------------------------------------------------------ desenho
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        if self.phase is Phase.INTRO:
            self._draw_intro(surface)
            return
        world = self.world
        phase = self.phase
        flashing = phase is Phase.CLEARED and self.elapsed >= self.CLEAR_FREEZE
        if flashing and int((self.elapsed - self.CLEAR_FREEZE) / 0.25) % 2 == 0:
            surface.blit(self.walls_flash, (0, MAZE_Y))
        else:
            surface.blit(self.walls, (0, MAZE_Y))

        if not flashing:
            self._draw_food(surface)
        self._draw_bonus(surface)

        hide_ghosts = (phase is Phase.DYING and self.elapsed >= self.DEATH_FREEZE) or flashing or phase is Phase.GAME_OVER
        if not hide_ghosts:
            for ghost in world.ghosts:
                self._draw_ghost(surface, ghost)
        if phase is not Phase.GAME_OVER:
            self._draw_coachman(surface)

        if world.eaten_ghost is not None:
            ghost, points = world.eaten_ghost
            draw_text(surface, self.app.assets, str(points), 8, CYAN, (ghost.x, ghost.y + MAZE_Y))
        for text, x, y, _ in self.popups.items:
            draw_text(surface, self.app.assets, text, 8, (255, 184, 255), (x, y + MAZE_Y))

        definition = world.maze.definition
        ready_y = (definition.bonus_position[1]) * TILE + MAZE_Y
        if phase is Phase.READY:
            draw_text(surface, self.app.assets, "READY!", 16, YELLOW, (SCREEN_W / 2, ready_y))
        elif phase is Phase.GAME_OVER:
            draw_text(surface, self.app.assets, "GAME  OVER", 16, RED, (SCREEN_W / 2, ready_y))

        if self.debug and phase is Phase.PLAYING:
            draw_debug(surface, self.app.assets, world)
        self._draw_hud(surface)

    @staticmethod
    def _minimap(maze) -> pygame.Surface:
        cell = TILE // 2
        surf = pygame.Surface((maze.cols * cell, maze.rows * cell))
        color = maze.definition.wall_color
        dark = tuple(c // 3 for c in color)
        for c, r in maze.walls:
            surf.fill(dark, (c * cell, r * cell, cell, cell))
            surf.fill(color, (c * cell + 1, r * cell + 1, cell - 2, cell - 2))
        for c, r in maze.doors:
            surf.fill((255, 184, 255), (c * cell, r * cell + cell // 2 - 1, cell, 2))
        for c, r in maze.dots:
            surf.fill((110, 235, 120), (c * cell + 3, r * cell + 3, 2, 2))
        for c, r in maze.energizers:
            surf.fill((255, 255, 255), (c * cell + 2, r * cell + 2, 4, 4))
        return surf

    def _draw_intro(self, surface: pygame.Surface) -> None:
        """Cartão de apresentação da fase (labirinto, nome e power-ups sorteados)."""
        a = self.app.assets
        definition = self.world.maze.definition
        draw_text(surface, a, f"FASE {self.session.level}", 32, YELLOW, (SCREEN_W / 2, 64), shadow=(80, 60, 0))
        draw_text(surface, a, definition.name, 16, definition.wall_color, (SCREEN_W / 2, 112))
        draw_text(surface, a, definition.subtitle, 8, (255, 184, 255), (SCREEN_W / 2, 138))
        thumb = self.thumbnail.get_rect(center=(SCREEN_W // 2, 290))
        surface.blit(self.thumbnail, thumb)
        draw_text(surface, a, "POWER-UPS DESTA FASE", 8, WHITE, (SCREEN_W / 2, thumb.bottom + 26))
        icons = [icon for _, icon in sorted(self.world.maze.energizers.items())]
        for i, icon in enumerate(icons):
            x = SCREEN_W / 2 + (i - (len(icons) - 1) / 2) * 40
            surface.blit(a.frame(f"powerup.{icon}"), (round(x - SPRITE / 2), thumb.bottom + 40))
        if self.session.level > 1 and self.world.spec.fright_time < 3:
            draw_text(surface, a, "AS CADEIRAS ESTAO MAIS ESPERTAS!", 8, (255, 90, 90), (SCREEN_W / 2, SCREEN_H - 40))

    def _blit_sprite(self, surface: pygame.Surface, frame: pygame.Surface, x: float, y: float) -> None:
        surface.blit(frame, (round(x - SPRITE / 2), round(y - SPRITE / 2 + MAZE_Y)))

    def _render_food(self, size: tuple[int, int]) -> pygame.Surface:
        """Os "$" ficam numa camada pronta; comer um só apaga aquele tile."""
        layer = pygame.Surface(size, pygame.SRCALPHA)
        dollar = self.app.assets.frame("dot.dollar")
        ox, oy = (TILE - DOLLAR_SIZE[0]) // 2, (TILE - DOLLAR_SIZE[1]) // 2
        for c, r in self.world.maze.dots:
            layer.blit(dollar, (c * TILE + ox, r * TILE + oy))
        return layer

    def _erase_dot(self, event: DotEaten) -> None:
        c, r = event.tile
        self.food_layer.fill((0, 0, 0, 0), (c * TILE, r * TILE, TILE, TILE))

    def _draw_food(self, surface: pygame.Surface) -> None:
        surface.blit(self.food_layer, (0, MAZE_Y))
        # power-ups piscam durante o jogo, como os energizadores do arcade
        blink_off = self.phase is Phase.PLAYING and (self.frame // 10) % 2 == 1
        if not blink_off:
            for (c, r), icon in self.world.maze.energizers.items():
                frame = self.app.assets.frame(f"powerup.{icon}")
                surface.blit(frame, (c * TILE + TILE // 2 - SPRITE // 2, r * TILE + TILE // 2 - SPRITE // 2 + MAZE_Y))

    def _draw_bonus(self, surface: pygame.Surface) -> None:
        bonus = self.world.bonus
        if bonus.active:
            self._blit_sprite(surface, self.app.assets.frame("bonus.vovo"), bonus.x, bonus.y)

    def _draw_coachman(self, surface: pygame.Surface) -> None:
        pac = self.world.coachman
        assets = self.app.assets
        if self.world.eaten_ghost is not None:
            return  # some durante a pausa de "comeu cadeira", como no arcade
        if self.phase is Phase.DYING and self.elapsed >= self.DEATH_FREEZE:
            frames = assets.frames("coachman.death")
            t = (self.elapsed - self.DEATH_FREEZE) / self.DEATH_ANIM
            index = min(len(frames) - 1, int(t * len(frames)))
            self._blit_sprite(surface, frames[index], pac.x, pac.y)
            return
        anim = 2 if self.phase is Phase.READY else pac.anim_frame
        frame = assets.frame(f"coachman.{pac.direction.name.lower()}.{anim}")
        self._blit_sprite(surface, frame, pac.x, pac.y)

    def _ghost_frame(self, ghost: Ghost) -> pygame.Surface:
        assets = self.app.assets
        spin = ghost.spin_frame
        if ghost.state in (gs.EATEN, gs.ENTERING_HOUSE):
            return assets.frame(f"ghost.eaten.{spin}")
        if ghost.frightened:
            look = "flash" if self.world.modes.flashing else "frightened"
            return assets.frame(f"ghost.{look}.{spin}")
        return assets.frame(f"ghost.{ghost.name}.{spin}")

    def _draw_ghost(self, surface: pygame.Surface, ghost: Ghost) -> None:
        if self.world.eaten_ghost is not None and self.world.eaten_ghost[0] is ghost:
            return
        y = ghost.y
        if ghost.state is not gs.IN_HOUSE:
            y += math.sin((self.frame + HOVER_PHASE[ghost.name]) / 6) * 1.2  # flutuando no ar
            self._draw_trail(surface, ghost, y)
        self._blit_sprite(surface, self._ghost_frame(ghost), ghost.x, y)

    def _draw_trail(self, surface: pygame.Surface, ghost: Ghost, y: float) -> None:
        """Rastro de cadeira voadora: riscos atrás dela, contra o movimento."""
        if ghost.state in (gs.EATEN, gs.ENTERING_HOUSE) or self.phase is not Phase.PLAYING:
            return
        color = (90, 90, 255) if ghost.frightened else GHOST_COLORS[ghost.name]
        d = ghost.direction
        back_x, back_y = -d.dx, -d.dy
        side_x, side_y = d.dy, d.dx
        wobble = (self.frame // 3) % 3
        for i, offset in enumerate((-6, 0, 6)):
            start = 13 + (wobble + i) % 3 * 2
            length = 6 - abs(offset) // 3
            x0 = ghost.x + back_x * start + side_x * offset
            y0 = y + back_y * start + side_y * offset + MAZE_Y
            x1 = x0 + back_x * length
            y1 = y0 + back_y * length
            pygame.draw.line(surface, color, (round(x0), round(y0)), (round(x1), round(y1)), 1)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        assets = self.app.assets
        session = self.session
        if self.phase is not Phase.PLAYING or (self.frame // 16) % 2 == 0:
            draw_text(surface, assets, "1UP", 16, WHITE, (3 * TILE, 0), "topleft")
        draw_text(surface, assets, "HIGH SCORE", 16, WHITE, (SCREEN_W / 2, 0), "midtop")
        draw_text(surface, assets, f"{session.score:>2}", 16, WHITE, (7 * TILE, TILE), "topright")
        if session.high_score:
            draw_text(surface, assets, f"{session.high_score}", 16, WHITE, (17 * TILE, TILE), "topright")
        definition = self.world.maze.definition
        label = f"FASE {session.level} - {definition.name}"
        draw_text(surface, assets, label, 8, definition.wall_color, (SCREEN_W / 2, 2 * TILE + 5), "midtop")

        base_y = SCREEN_H - 2 * TILE
        reserve = session.lives - 1  # a vida em jogo não aparece embaixo
        life = assets.frame("coachman.left.1")
        for i in range(max(0, min(reserve, 6))):
            surface.blit(life, (2 * TILE + i * 2 * TILE - SPRITE // 2 + TILE // 2, base_y + 1))
        vovo = assets.frame("bonus.vovo")
        for i in range(min(session.level, 7)):
            surface.blit(vovo, (SCREEN_W - 3 * TILE - i * 2 * TILE - SPRITE // 2 + TILE // 2, base_y + 1))
        if self.app.audio.muted:
            draw_text(surface, assets, "MUDO", 8, (150, 150, 150), (SCREEN_W / 2, SCREEN_H - 6), "midbottom")
        if self.phase is Phase.PLAYING:  # botão de pausa (toque/clique)
            x, y, w, h = PAUSE_BUTTON
            for dx in (-5, 2):
                surface.fill((120, 120, 140), (x + w // 2 + dx, y + 10, 3, 12))
