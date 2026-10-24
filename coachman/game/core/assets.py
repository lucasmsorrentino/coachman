"""Carregamento e cache de recursos -- padrão **Flyweight** (GoF, p. 195).

Os quadros de animação (estado *intrínseco*: os pixels) são carregados uma
única vez do atlas ``sprites.png`` e compartilhados por todas as entidades;
cada cadeira guarda só o seu estado *extrínseco* (posição, quadro atual).
O mesmo vale para fontes e textos já renderizados.

Referência: https://gameprogrammingpatterns.com/flyweight.html
"""
from __future__ import annotations

import json
from pathlib import Path

import pygame

from ..config import FONT_FILE


class AssetLibrary:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self._frames: dict[str, pygame.Surface] = {}
        self._images: dict[str, pygame.Surface] = {}
        self._fonts: dict[int, pygame.font.Font] = {}
        self._texts: dict[tuple, pygame.Surface] = {}

    def path(self, relative: str) -> str:
        return str(self.base_dir / relative)

    # ------------------------------------------------------------------ sprites
    def load_atlas(self, image: str = "assets/sprites/sprites.png", index: str = "assets/sprites/sprites.json") -> None:
        sheet = pygame.image.load(self.path(image))
        if pygame.display.get_surface() is not None:
            sheet = sheet.convert_alpha()
        with open(self.path(index), encoding="utf-8") as fh:
            rects = json.load(fh)
        for name, (x, y, w, h) in rects.items():
            self._frames[name] = sheet.subsurface(pygame.Rect(x, y, w, h))

    def frame(self, name: str) -> pygame.Surface:
        return self._frames[name]

    def frames(self, prefix: str) -> list[pygame.Surface]:
        """Todos os quadros ``prefix.0``, ``prefix.1``... em ordem."""
        out, i = [], 0
        while f"{prefix}.{i}" in self._frames:
            out.append(self._frames[f"{prefix}.{i}"])
            i += 1
        return out

    def image(self, relative: str) -> pygame.Surface:
        if relative not in self._images:
            img = pygame.image.load(self.path(relative))
            if pygame.display.get_surface() is not None:
                img = img.convert()
            self._images[relative] = img
        return self._images[relative]

    # ------------------------------------------------------------------ texto
    def font(self, size: int) -> pygame.font.Font:
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(self.path(FONT_FILE), size)
        return self._fonts[size]

    def text(self, text: str, size: int, color: tuple[int, int, int]) -> pygame.Surface:
        key = (text, size, color)
        surf = self._texts.get(key)
        if surf is None:
            if len(self._texts) > 512:  # cache simples, sem crescer para sempre
                self._texts.clear()
            surf = self.font(size).render(text, False, color)
            self._texts[key] = surf
        return surf
