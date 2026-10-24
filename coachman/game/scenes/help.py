"""Como jogar + resumo da IA das cadeiras ("Mentoria gratuita")."""
from __future__ import annotations

import pygame

from ..actors.factory import PROFILES
from ..config import CYAN, SCREEN_H, SCREEN_W, SPRITE, WHITE, YELLOW
from ..core.scenes import Scene
from ..ui.text import draw_text

GHOST_LINES = {
    "blinky": ("BLINKY - PERSEGUIDORA", "MIRA EXATAMENTE VOCE."),
    "pinky": ("PINKY - EMBOSCADA", "MIRA 4 TILES A SUA FRENTE."),
    "inky": ("INKY - IMPREVISIVEL", "USA O BLINKY PARA TE CERCAR."),
    "clyde": ("CLYDE - DESLIGADA", "PERTO DEMAIS? FOGE PRO CANTO."),
}


class HelpScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.time = 0.0

    def update(self, dt: float) -> None:
        self.time += dt

    def on_confirm(self) -> None:
        self.app.scenes.pop()

    on_back = on_confirm

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        a = self.app.assets
        spin = int(self.time * 8) % 8
        draw_text(surface, a, "COMO JOGAR", 16, YELLOW, (SCREEN_W / 2, 24))
        controls = (
            "SETAS / WASD / DESLIZAR: MOVER",
            "P/ESC OU TOQUE NO 'II': PAUSA   M: SOM",
            "TAB OU SEGURAR O DEDO: RAIO-X DA IA",
        )
        for i, line in enumerate(controls):
            draw_text(surface, a, line, 8, WHITE, (SCREEN_W / 2, 52 + i * 14))

        # itens
        y = 112
        surface.blit(a.frame("dot.dollar"), (40, y - 4))
        draw_text(surface, a, "10", 8, WHITE, (56, y), "midleft")
        for i in range(4):
            surface.blit(a.frame(f"powerup.{(i + int(self.time)) % 7}"), (100 + i * 22, y - 15))
        draw_text(surface, a, "50", 8, WHITE, (196, y), "midleft")
        surface.blit(a.frame("bonus.vovo"), (236, y - 15))
        draw_text(surface, a, "VOVO = BONUS", 8, WHITE, (272, y), "midleft")
        draw_text(surface, a, "COMA UM POWER-UP E DEVORE AS CADEIRAS:", 8, CYAN, (SCREEN_W / 2, y + 30))
        draw_text(surface, a, "200 - 400 - 800 - 1600", 8, CYAN, (SCREEN_W / 2, y + 46))

        draw_text(surface, a, "AS CADEIRAS VOADORAS", 16, YELLOW, (SCREEN_W / 2, 204))
        for i, profile in enumerate(PROFILES):
            gy = 240 + i * 48
            surface.blit(a.frame(f"ghost.{profile.name}.{(spin + i * 2) % 8}"), (28, gy - SPRITE // 2))
            title, desc = GHOST_LINES[profile.name]
            draw_text(surface, a, title, 8, WHITE, (72, gy - 7), "midleft")
            draw_text(surface, a, desc, 8, (180, 180, 180), (72, gy + 9), "midleft")

        notes = (
            "ELAS ALTERNAM ENTRE DISPERSAO (CADA UMA",
            "VAI PRO SEU CANTO) E PERSEGUICAO.",
            "AZUIS = ASSUSTADAS. BRANCAS = VAI ACABAR!",
        )
        for i, line in enumerate(notes):
            draw_text(surface, a, line, 8, (255, 184, 255), (SCREEN_W / 2, 440 + i * 16))
        draw_text(surface, a, "ENTER / TOQUE: VOLTAR", 8, WHITE, (SCREEN_W / 2, SCREEN_H - 24))
