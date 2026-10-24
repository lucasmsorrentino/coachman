"""Tela de título com o menu original (mesmos textos da versão em Python)."""
from __future__ import annotations

import pygame

from ..config import RED, SCREEN_H, SCREEN_W, WHITE, YELLOW
from ..core.scenes import Scene
from ..ui.text import draw_text
from ..world.direction import Direction

# (rótulo, subtítulo) -- os três primeiros são os da versão original
MENU = (
    (">Play<", "Murro no fucin"),
    (">Score<", "Prosperidade Desbloqueada"),
    (">Help<", "Mentoria gratuita"),
    (">Exit<", "Vc não é homi pa isso"),
)


class TitleScene(Scene):
    music = "menu"

    def __init__(self, app) -> None:
        super().__init__(app)
        self.selected = 0
        self.time = 0.0

    def update(self, dt: float) -> None:
        self.time += dt

    def on_direction(self, direction: Direction) -> None:
        if direction in (Direction.UP, Direction.DOWN):
            self.selected = (self.selected + direction.dy) % len(MENU)
            self.app.audio.play_sfx("menu_move")

    def on_confirm(self) -> None:
        self.app.audio.play_sfx("menu_select")
        if self.selected == 0:
            from .play import PlayScene

            self.app.scenes.replace(PlayScene(self.app))
        elif self.selected == 1:
            from .highscores import HighScoresScene

            self.app.scenes.push(HighScoresScene(self.app))
        elif self.selected == 2:
            from .help import HelpScene

            self.app.scenes.push(HelpScene(self.app))
        else:
            from .exit import ExitScene

            self.app.scenes.push(ExitScene(self.app))

    def resume(self) -> None:
        self.app.audio.play_music(self.music)

    def draw(self, surface: pygame.Surface) -> None:
        a = self.app.assets
        surface.blit(a.image("assets/images/title.png"), (0, 0))
        draw_text(surface, a, "COACH-MAN", 40, YELLOW, (SCREEN_W / 2, 56), shadow=(0, 0, 0))

        panel_top = 300
        panel = pygame.Surface((SCREEN_W - 48, SCREEN_H - panel_top - 40), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 185))
        surface.blit(panel, (24, panel_top))
        pygame.draw.rect(surface, YELLOW, (24, panel_top, SCREEN_W - 48, SCREEN_H - panel_top - 40), 2)

        for i, (label, subtitle) in enumerate(MENU):
            y = panel_top + 34 + i * 50
            chosen = i == self.selected
            color = RED if chosen else YELLOW
            draw_text(surface, a, label, 20 if chosen else 16, color, (SCREEN_W / 2, y), shadow=(0, 0, 0))
            draw_text(surface, a, subtitle, 8, WHITE if chosen else (200, 200, 200), (SCREEN_W / 2, y + 20))

        hint = "SETAS/DESLIZE + ENTER/TOQUE" if int(self.time * 2) % 2 == 0 else "M: SOM   TAB: RAIO-X DA IA"
        draw_text(surface, a, hint, 8, WHITE, (SCREEN_W / 2, SCREEN_H - 22), shadow=(0, 0, 0))
