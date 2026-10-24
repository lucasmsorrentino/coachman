"""Placar dos 10 melhores ("Prosperidade Desbloqueada")."""
from __future__ import annotations

import pygame

from ..config import CYAN, RED, SCREEN_H, SCREEN_W, WHITE, YELLOW
from ..core.scenes import Scene
from ..persistence.highscores import ScoreEntry
from ..ui.text import draw_text


class HighScoresScene(Scene):
    music = "highscores"

    def __init__(self, app, highlight: ScoreEntry | None = None) -> None:
        super().__init__(app)
        self.highlight = highlight
        self.time = 0.0
        self.entries = app.scores.top()

    def update(self, dt: float) -> None:
        self.time += dt

    def _leave(self) -> None:
        from .title import TitleScene

        if len(self.app.scenes) > 1:
            self.app.scenes.pop()
        else:
            self.app.scenes.replace(TitleScene(self.app))

    def on_confirm(self) -> None:
        if self.time > 0.4:
            self._leave()

    on_back = on_confirm
    on_pause = on_confirm

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        a = self.app.assets
        draw_text(surface, a, "HIGH SCORES", 24, YELLOW, (SCREEN_W / 2, 48), shadow=(80, 60, 0))
        draw_text(surface, a, "PROSPERIDADE DESBLOQUEADA", 8, CYAN, (SCREEN_W / 2, 78))
        draw_text(surface, a, "POS  NOME   SCORE  FASE", 8, (160, 160, 160), (SCREEN_W / 2, 112))
        if not self.entries:
            draw_text(surface, a, "NINGUEM AINDA...", 16, WHITE, (SCREEN_W / 2, 220))
            draw_text(surface, a, "SEJA O PRIMEIRO COACH!", 8, WHITE, (SCREEN_W / 2, 250))
        for i, e in enumerate(self.entries):
            y = 140 + i * 32
            mine = self.highlight is not None and e == self.highlight
            if mine and int(self.time * 4) % 2:
                continue
            color = RED if mine else (YELLOW if i == 0 else WHITE)
            line = f"{i + 1:>2}.  {e.initials:<3}  {e.score:>7}   {e.level:>2}"
            draw_text(surface, a, line, 16, color, (SCREEN_W / 2, y))
        if int(self.time * 2) % 2 == 0:
            draw_text(surface, a, "APERTE ENTER / TOQUE", 8, WHITE, (SCREEN_W / 2, SCREEN_H - 40))
