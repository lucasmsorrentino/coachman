"""Entrada do jogador -- padrão **Command** (GoF, "Command", p. 233).

Teclado, toque na tela (deslizar/tocar) e controle viram *objetos comando*
(``DirectionCommand``, ``ConfirmCommand``...). A cena ativa recebe o comando e
o executa sobre si mesma (``command.execute(scene)``). Benefícios:

* trocar o mapeamento de teclas não mexe em nenhuma cena;
* o mesmo comando serve para o labirinto (mover o Coach-Man) e para os menus
  (mover a seleção);
* testes podem "apertar botões" criando comandos diretamente.

Referência: Robert Nystrom, *Game Programming Patterns*,
https://gameprogrammingpatterns.com/command.html
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import pygame

from ..config import PAUSE_BUTTON
from ..world.direction import Direction


class CommandTarget:
    """Interface do *receiver*. As cenas sobrescrevem só o que usam."""

    def on_direction(self, direction: Direction) -> None: ...
    def on_confirm(self) -> None: ...
    def on_back(self) -> None: ...
    def on_pause(self) -> None: ...
    def on_toggle_debug(self) -> None: ...
    def on_text(self, char: str) -> None: ...
    def on_erase(self) -> None: ...


class Command(ABC):
    @abstractmethod
    def execute(self, target: CommandTarget) -> None: ...


class DirectionCommand(Command):
    def __init__(self, direction: Direction) -> None:
        self.direction = direction

    def execute(self, target: CommandTarget) -> None:
        target.on_direction(self.direction)

    def __repr__(self) -> str:
        return f"DirectionCommand({self.direction.name})"


class ConfirmCommand(Command):
    def execute(self, target: CommandTarget) -> None:
        target.on_confirm()


class BackCommand(Command):
    def execute(self, target: CommandTarget) -> None:
        target.on_back()


class PauseCommand(Command):
    def execute(self, target: CommandTarget) -> None:
        target.on_pause()


class ToggleDebugCommand(Command):
    def execute(self, target: CommandTarget) -> None:
        target.on_toggle_debug()


class TextCommand(Command):
    def __init__(self, char: str) -> None:
        self.char = char

    def execute(self, target: CommandTarget) -> None:
        target.on_text(self.char)


class EraseCommand(Command):
    def execute(self, target: CommandTarget) -> None:
        target.on_erase()


class AppCommand(Command):
    """Comandos globais, tratados pela aplicação e não pela cena."""

    def __init__(self, action: str) -> None:
        self.action = action  # "mute" | "fullscreen"

    def execute(self, target: CommandTarget) -> None:  # pragma: no cover - tratado pelo App
        pass


# Os comandos não guardam estado mutável: uma instância de cada basta.
UP, DOWN, LEFT, RIGHT = (DirectionCommand(d) for d in (Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT))
CONFIRM, BACK, PAUSE, DEBUG, ERASE = ConfirmCommand(), BackCommand(), PauseCommand(), ToggleDebugCommand(), EraseCommand()
MUTE, FULLSCREEN = AppCommand("mute"), AppCommand("fullscreen")

DEFAULT_KEYMAP: dict[int, Command] = {
    pygame.K_UP: UP, pygame.K_w: UP,
    pygame.K_DOWN: DOWN, pygame.K_s: DOWN,
    pygame.K_LEFT: LEFT, pygame.K_a: LEFT,
    pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT,
    pygame.K_RETURN: CONFIRM, pygame.K_KP_ENTER: CONFIRM, pygame.K_SPACE: CONFIRM,
    pygame.K_ESCAPE: BACK,
    pygame.K_p: PAUSE,
    pygame.K_TAB: DEBUG, pygame.K_x: DEBUG,
    pygame.K_BACKSPACE: ERASE,
    pygame.K_m: MUTE,
    pygame.K_F11: FULLSCREEN, pygame.K_f: FULLSCREEN,
}


class InputHandler:
    """Traduz eventos crus do pygame em comandos (o *invoker* do padrão).

    ``text_mode`` liga a digitação de letras (tela de iniciais); nesse modo
    as letras deixam de acionar atalhos como W/A/S/D.
    """

    SWIPE_MIN = 18  # px (na resolução lógica) para considerar um deslize
    TAP_MAX = 8
    LONG_PRESS_MS = 600  # segurar o dedo parado = liga/desliga o Raio-X

    def __init__(self, keymap: dict[int, Command] | None = None) -> None:
        self.keymap = dict(keymap or DEFAULT_KEYMAP)
        self.text_mode = False
        self._touch_origin: tuple[float, float] | None = None
        self._touch_moved = False
        self._touch_started = 0
        self._swipe_sent: Command | None = None  # um comando por direção em cada gesto

    def translate(self, event: pygame.event.Event) -> list[Command]:
        if event.type == pygame.KEYDOWN:
            if self.text_mode and event.unicode and event.unicode.isalnum():
                return [TextCommand(event.unicode.upper())]
            command = self.keymap.get(event.key)
            return [command] if command else []

        if event.type == pygame.JOYHATMOTION:
            x, y = event.value
            if x or y:
                return [{(0, 1): UP, (0, -1): DOWN, (-1, 0): LEFT, (1, 0): RIGHT}.get((x, y), UP if y > 0 else DOWN)]
        if event.type == pygame.JOYBUTTONDOWN:
            return [CONFIRM if event.button == 0 else PAUSE if event.button in (6, 7, 9) else BACK]

        # Toque / mouse: deslizar = direção, toque curto = confirmar,
        # toque longo = Raio-X (no celular não existe a tecla TAB).
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._touch_origin, self._touch_moved = event.pos, False
            self._touch_started = pygame.time.get_ticks()
            self._swipe_sent = None
        elif event.type == pygame.MOUSEMOTION and self._touch_origin is not None:
            dx = event.pos[0] - self._touch_origin[0]
            dy = event.pos[1] - self._touch_origin[1]
            if max(abs(dx), abs(dy)) >= self.SWIPE_MIN:
                self._touch_origin, self._touch_moved = event.pos, True
                if abs(dx) > abs(dy):
                    command = RIGHT if dx > 0 else LEFT
                else:
                    command = DOWN if dy > 0 else UP
                if command is not self._swipe_sent:
                    self._swipe_sent = command
                    return [command]
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self._touch_origin is not None:
            dx = event.pos[0] - self._touch_origin[0]
            dy = event.pos[1] - self._touch_origin[1]
            still = not self._touch_moved and max(abs(dx), abs(dy)) <= self.TAP_MAX
            held = pygame.time.get_ticks() - self._touch_started
            self._touch_origin = None
            if still:
                if pygame.Rect(PAUSE_BUTTON).collidepoint(event.pos):
                    return [PAUSE]  # botão de pausa desenhado no canto do placar
                return [DEBUG if held >= self.LONG_PRESS_MS else CONFIRM]
        return []
