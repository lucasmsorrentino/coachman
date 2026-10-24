"""Atalhos para escrever texto com a fonte Press Start 2P."""
from __future__ import annotations

import pygame

from ..core.assets import AssetLibrary


def draw_text(
    surface: pygame.Surface,
    assets: AssetLibrary,
    text: str,
    size: int,
    color: tuple[int, int, int],
    pos: tuple[float, float],
    anchor: str = "center",
    shadow: tuple[int, int, int] | None = None,
) -> pygame.Rect:
    """Desenha ``text`` com o ponto ``pos`` no ``anchor`` dado (center, topleft...)."""
    surf = assets.text(text, size, color)
    rect = surf.get_rect(**{anchor: (round(pos[0]), round(pos[1]))})
    if shadow is not None:
        shade = assets.text(text, size, shadow)
        step = max(1, size // 8)
        for dx, dy in ((step, step), (-step, 0), (step, 0), (0, -step), (0, step)):
            surface.blit(shade, rect.move(dx, dy))
    surface.blit(surf, rect)
    return rect


def draw_lines(
    surface: pygame.Surface,
    assets: AssetLibrary,
    lines: list[str],
    size: int,
    color: tuple[int, int, int],
    top_left: tuple[float, float],
    spacing: float = 1.6,
) -> float:
    """Várias linhas alinhadas à esquerda; devolve o y logo abaixo da última."""
    x, y = top_left
    for line in lines:
        if line:
            draw_text(surface, assets, line, size, color, (x, y), anchor="topleft")
        y += size * spacing
    return y
