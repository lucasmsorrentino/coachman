"""Barramento de eventos -- padrão **Observer** (GoF, "Observer", p. 293).

Quem gera um acontecimento do jogo (o ``World``) apenas *publica* um evento;
quem se interessa por ele *assina* aquele tipo de evento. Assim placar, som,
casa dos fantasmas e HUD reagem a "comeu um $" sem que o código de movimento
conheça nenhum deles.

Referências:
* Gamma, Helm, Johnson, Vlissides. *Design Patterns* (1994) -- Observer.
* Robert Nystrom, *Game Programming Patterns* -- https://gameprogrammingpatterns.com/observer.html
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

E = TypeVar("E")
Handler = Callable[[Any], None]


class EventBus:
    """*Subject* genérico e tipado: os assinantes escolhem a classe do evento."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: type[E], handler: Callable[[E], None]) -> Callable[[], None]:
        self._handlers[event_type].append(handler)

        def unsubscribe() -> None:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)

        return unsubscribe

    def publish(self, event: object) -> None:
        # cópia da lista: um assinante pode se desinscrever durante o aviso
        for handler in list(self._handlers[type(event)]):
            handler(event)

    def clear(self) -> None:
        self._handlers.clear()


# --------------------------------------------------------------------------
# Eventos do jogo (objetos imutáveis, só dados)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class DotEaten:
    tile: tuple[int, int]
    food_left: int


@dataclass(frozen=True)
class EnergizerEaten:
    tile: tuple[int, int]
    food_left: int


@dataclass(frozen=True)
class GhostEaten:
    ghost: str
    points: int
    position: tuple[float, float]


@dataclass(frozen=True)
class CoachManCaught:
    ghost: str


@dataclass(frozen=True)
class BonusSpawned:
    position: tuple[float, float]


@dataclass(frozen=True)
class BonusEaten:
    points: int
    position: tuple[float, float]


@dataclass(frozen=True)
class ModeChanged:
    mode: str  # "scatter" ou "chase"


@dataclass(frozen=True)
class FrightStarted:
    seconds: float


@dataclass(frozen=True)
class FrightEnded:
    pass


@dataclass(frozen=True)
class ExtraLife:
    lives: int


@dataclass(frozen=True)
class LevelCleared:
    level: int
