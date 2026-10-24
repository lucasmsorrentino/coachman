"""Novo recorde: entrada de 3 iniciais no estilo arcade.

Funciona com teclado (digitando as letras ou com as setas), controle e toque
(deslizar para cima/baixo troca a letra, tocar avança).
"""
from __future__ import annotations

import pygame

from ..config import CYAN, RED, SCREEN_H, SCREEN_W, WHITE, YELLOW
from ..core.scenes import Scene
from ..persistence.highscores import ScoreEntry
from ..ui.text import draw_text
from ..world.direction import Direction

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


class InitialsScene(Scene):
    music = "highscores"

    def __init__(self, app, score: int, level: int) -> None:
        super().__init__(app)
        self.score = score
        self.level = level
        self.letters = [0, 0, 0]
        self.cursor = 0
        self.time = 0.0

    def enter(self) -> None:
        super().enter()
        self.app.input.text_mode = True

    def exit(self) -> None:
        self.app.input.text_mode = False

    def update(self, dt: float) -> None:
        self.time += dt

    @property
    def initials(self) -> str:
        return "".join(ALPHABET[i] for i in self.letters)

    def on_direction(self, direction: Direction) -> None:
        if direction is Direction.UP:
            self.letters[self.cursor] = (self.letters[self.cursor] + 1) % len(ALPHABET)
        elif direction is Direction.DOWN:
            self.letters[self.cursor] = (self.letters[self.cursor] - 1) % len(ALPHABET)
        elif direction is Direction.LEFT:
            self.cursor = max(0, self.cursor - 1)
        else:
            self.cursor = min(2, self.cursor + 1)

    def on_text(self, char: str) -> None:
        if char in ALPHABET:
            self.letters[self.cursor] = ALPHABET.index(char)
            if self.cursor < 2:
                self.cursor += 1

    def on_erase(self) -> None:
        self.cursor = max(0, self.cursor - 1)

    def on_confirm(self) -> None:
        if self.cursor < 2:
            self.cursor += 1
            return
        from .highscores import HighScoresScene

        entry = ScoreEntry.new(self.initials, self.score, self.level)
        self.app.scores.add(entry)
        self.app.scenes.replace(HighScoresScene(self.app, highlight=entry))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        a = self.app.assets
        draw_text(surface, a, "NOVO RECORDE!", 24, YELLOW, (SCREEN_W / 2, 90), shadow=(80, 60, 0))
        draw_text(surface, a, f"SCORE {self.score}", 16, WHITE, (SCREEN_W / 2, 150))
        draw_text(surface, a, "DIGITE SUAS INICIAIS", 8, CYAN, (SCREEN_W / 2, 200))
        for i, index in enumerate(self.letters):
            x = SCREEN_W / 2 + (i - 1) * 56
            active = i == self.cursor
            color = RED if active else WHITE
            draw_text(surface, a, ALPHABET[index], 32, color, (x, 270))
            if active and int(self.time * 3) % 2 == 0:
                pygame.draw.rect(surface, RED, (x - 18, 296, 36, 4))
                draw_text(surface, a, "↑", 8, RED, (x, 236))
                draw_text(surface, a, "↓", 8, RED, (x, 312))
        lines = ("LETRAS OU ↑↓: ESCOLHER", "←→: MOVER   ENTER/TOQUE: OK")
        for i, line in enumerate(lines):
            draw_text(surface, a, line, 8, (180, 180, 180), (SCREEN_W / 2, SCREEN_H - 120 + i * 18))
