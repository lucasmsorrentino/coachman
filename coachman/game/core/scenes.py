"""Telas do jogo -- padrão **State** (GoF, "State", p. 305) com pilha.

Cada tela (título, jogo, placar, ajuda...) é um *estado* da aplicação: tem
seus próprios ``update``, ``draw`` e reação aos comandos. A aplicação só
conversa com "a cena do topo", sem ``if menu: ... elif jogo: ...``.

A pilha (``SceneStack``) é o "autômato com pilha" descrito por Nystrom: a
pausa é empilhada *sobre* o jogo e, ao sair, o jogo continua exatamente de
onde parou. Referência: https://gameprogrammingpatterns.com/state.html
(seção *Pushdown Automata*).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from .commands import CommandTarget

if TYPE_CHECKING:  # pragma: no cover
    from ..app import App


class Scene(CommandTarget):
    #: se True, a cena de baixo continua sendo desenhada (overlays, ex.: pausa)
    transparent = False
    #: música a tocar enquanto a cena está ativa (None = não mexe)
    music: str | None = None

    def __init__(self, app: "App") -> None:
        self.app = app

    def enter(self) -> None:
        if self.music:
            self.app.audio.play_music(self.music)

    def exit(self) -> None: ...

    def resume(self) -> None:
        """Chamado quando a cena volta ao topo (a de cima foi removida)."""

    def update(self, dt: float) -> None: ...

    def draw(self, surface: pygame.Surface) -> None: ...


class SceneStack:
    def __init__(self) -> None:
        self._stack: list[Scene] = []

    @property
    def top(self) -> Scene | None:
        return self._stack[-1] if self._stack else None

    def push(self, scene: Scene) -> None:
        self._stack.append(scene)
        scene.enter()

    def pop(self) -> Scene | None:
        if not self._stack:
            return None
        scene = self._stack.pop()
        scene.exit()
        if self.top:
            self.top.resume()
        return scene

    def replace(self, scene: Scene) -> None:
        """Troca toda a pilha por uma nova cena (ex.: menu -> jogo)."""
        while self._stack:
            self._stack.pop().exit()
        self.push(scene)

    def update(self, dt: float) -> None:
        if self.top:
            self.top.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        start = len(self._stack) - 1
        while start > 0 and self._stack[start].transparent:
            start -= 1
        for scene in self._stack[start:]:
            scene.draw(surface)

    def __len__(self) -> int:
        return len(self._stack)
