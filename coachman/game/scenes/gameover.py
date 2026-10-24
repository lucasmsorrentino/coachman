"""Fim de jogo: a imagem da ambulância (da versão original) e o placar final."""
from __future__ import annotations

import pygame

from ..config import RED, SCREEN_H, SCREEN_W, WHITE, YELLOW
from ..core.scenes import Scene
from ..ui.text import draw_text


class GameOverScene(Scene):
    DURATION = 5.0

    def __init__(self, app, score: int, level: int) -> None:
        super().__init__(app)
        self.score = score
        self.level = level
        self.elapsed = 0.0

    def enter(self) -> None:
        self.app.audio.stop_music()

    def update(self, dt: float) -> None:
        self.elapsed += dt
        if self.elapsed >= self.DURATION:
            self._next()

    def _next(self) -> None:
        from .highscores import HighScoresScene
        from .initials import InitialsScene

        if self.app.scores.qualifies(self.score):
            self.app.scenes.replace(InitialsScene(self.app, self.score, self.level))
        else:
            self.app.scenes.replace(HighScoresScene(self.app))

    def on_confirm(self) -> None:
        if self.elapsed > 1.0:
            self._next()

    on_back = on_confirm

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        a = self.app.assets
        image = a.image("assets/images/gameover.jpg")
        rect = image.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
        surface.blit(image, rect)
        draw_text(surface, a, "GAME OVER", 32, RED, (SCREEN_W / 2, rect.top - 60), shadow=(60, 0, 0))
        draw_text(surface, a, f"SCORE {self.score}", 16, YELLOW, (SCREEN_W / 2, rect.bottom + 36))
        draw_text(surface, a, f"CHEGOU NA FASE {self.level}", 8, WHITE, (SCREEN_W / 2, rect.bottom + 64))
