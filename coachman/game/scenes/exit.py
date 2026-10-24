"""">Exit< Vc não é homi pa isso".

No computador o jogo fecha depois da piada; no navegador não existe "sair"
(uma aba não pode se fechar sozinha), então a tela volta para o menu.
"""
from __future__ import annotations

import sys

import pygame

from ..config import RED, SCREEN_H, SCREEN_W, WHITE, YELLOW
from ..core.scenes import Scene
from ..ui.text import draw_text


class ExitScene(Scene):
    DESKTOP_DELAY = 2.5

    def __init__(self, app) -> None:
        super().__init__(app)
        self.time = 0.0
        self.web = sys.platform == "emscripten"

    def update(self, dt: float) -> None:
        self.time += dt
        if not self.web and self.time >= self.DESKTOP_DELAY:
            self.app.quit()

    def on_confirm(self) -> None:
        if self.web and self.time > 0.5:
            self.app.scenes.pop()

    on_back = on_confirm

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        a = self.app.assets
        image = a.image("assets/images/exit.png")
        surface.blit(image, image.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 40)))
        draw_text(surface, a, "VC NAO E HOMI", 24, RED, (SCREEN_W / 2, 90), shadow=(0, 0, 0))
        draw_text(surface, a, "PA ISSO!", 24, RED, (SCREEN_W / 2, 124), shadow=(0, 0, 0))
        if self.web:
            draw_text(surface, a, "NO NAVEGADOR NAO DA PRA FUGIR...", 8, WHITE, (SCREEN_W / 2, SCREEN_H - 110))
            draw_text(surface, a, "VOLTA PRO JOGO, CAMPEAO!", 8, YELLOW, (SCREEN_W / 2, SCREEN_H - 92))
            draw_text(surface, a, "ENTER / TOQUE", 8, WHITE, (SCREEN_W / 2, SCREEN_H - 50))
        else:
            draw_text(surface, a, "SAINDO...", 16, YELLOW, (SCREEN_W / 2, SCREEN_H - 90))
