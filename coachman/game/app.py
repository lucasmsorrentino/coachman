"""A aplicação: janela, laço principal e a pilha de telas.

Aqui também fica a **raiz de composição** (*Composition Root*, Mark Seemann,
*Dependency Injection in .NET*, 2011): é o único lugar que escolhe as
implementações concretas (áudio real ou nulo, SQLite ou localStorage) e as
entrega prontas para as telas. Nenhuma outra classe faz ``import`` de uma
implementação concreta para usá-la como global.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pygame

from .config import FPS, DT, SCREEN_H, SCREEN_W, TITLE
from .core.assets import AssetLibrary
from .core.audio import AudioService, create_audio
from .core.commands import AppCommand, InputHandler
from .core.loop import GameLoop
from .core.scenes import SceneStack
from .persistence.highscores import HighScoreRepository, create_repository

WEB = sys.platform == "emscripten"


class App:
    def __init__(
        self,
        base_dir: Path,
        audio: AudioService | None = None,
        scores: HighScoreRepository | None = None,
    ) -> None:
        pygame.init()
        flags = 0 if WEB else pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
        pygame.display.set_caption(TITLE)
        self.assets = AssetLibrary(base_dir)
        self.assets.load_atlas()
        try:
            pygame.display.set_icon(pygame.image.load(self.assets.path("assets/images/icon.png")))
        except pygame.error:  # pragma: no cover
            pass
        self.audio = audio or create_audio(base_dir)
        self.scores = scores or create_repository()
        self.input = InputHandler()
        self.scenes = SceneStack()
        self.clock = pygame.time.Clock()
        self.joysticks: list = []
        self.loop = GameLoop(DT, self.process_input, self.update, self.render, tick=lambda: self.clock.tick(FPS))

    async def run(self) -> None:
        from .scenes.title import TitleScene

        self.scenes.push(TitleScene(self))
        await self.loop.run()
        pygame.quit()

    def quit(self) -> None:
        self.loop.stop()

    # ------------------------------------------------------------------ laço
    def process_input(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            elif event.type == pygame.WINDOWFOCUSLOST:
                handler = getattr(self.scenes.top, "on_focus_lost", None)
                if handler:
                    handler()
            elif event.type == pygame.JOYDEVICEADDED:
                self.joysticks.append(pygame.joystick.Joystick(event.device_index))
            for command in self.input.translate(event):
                if isinstance(command, AppCommand):
                    self._app_command(command.action)
                elif self.scenes.top is not None:
                    command.execute(self.scenes.top)

    def _app_command(self, action: str) -> None:
        if action == "mute":
            self.audio.toggle_mute()
        elif action == "fullscreen":
            if WEB:
                try:
                    import platform as web

                    web.window.document.documentElement.requestFullscreen()
                except Exception:
                    pass
            else:
                pygame.display.toggle_fullscreen()

    def update(self, dt: float) -> None:
        self.scenes.update(dt)

    def render(self) -> None:
        self.screen.fill((0, 0, 0))
        self.scenes.draw(self.screen)
        pygame.display.flip()
