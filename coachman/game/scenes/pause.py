"""Pausa: cena "transparente" empilhada sobre o jogo (pushdown automaton)."""
from __future__ import annotations

import pygame

from ..config import SCREEN_H, SCREEN_W, WHITE, YELLOW
from ..core.scenes import Scene
from ..ui.text import draw_text


class PauseScene(Scene):
    transparent = True

    def enter(self) -> None:
        self.app.audio.pause_music()

    def exit(self) -> None:
        self.app.audio.resume_music()

    def draw(self, surface: pygame.Surface) -> None:
        shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 170))
        surface.blit(shade, (0, 0))
        a = self.app.assets
        draw_text(surface, a, "PAUSADO", 16, YELLOW, (SCREEN_W / 2, SCREEN_H / 2 - 24))
        draw_text(surface, a, "ENTER/P: CONTINUAR", 8, WHITE, (SCREEN_W / 2, SCREEN_H / 2 + 8))
        draw_text(surface, a, "ESC: VOLTAR AO MENU", 8, WHITE, (SCREEN_W / 2, SCREEN_H / 2 + 24))

    def on_confirm(self) -> None:
        self.app.scenes.pop()

    on_pause = on_confirm

    def on_back(self) -> None:
        from .title import TitleScene

        self.app.scenes.replace(TitleScene(self.app))
