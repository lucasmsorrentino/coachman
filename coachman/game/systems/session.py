"""Placar, vidas e fase de uma partida -- assinante (Observer) dos eventos.

Repare que ninguém chama ``session.add_points`` diretamente: o ``World``
publica "comeu um $" e a sessão, que assinou esse evento, soma 10 pontos.
"""
from __future__ import annotations

from ..config import DOT_POINTS, ENERGIZER_POINTS, EXTRA_LIFE_SCORE, START_LIVES
from ..core.events import BonusEaten, DotEaten, EnergizerEaten, EventBus, ExtraLife, GhostEaten


class Session:
    def __init__(self, bus: EventBus, high_score: int = 0, lives: int = START_LIVES) -> None:
        self.bus = bus
        self.score = 0
        self.high_score = high_score
        self.lives = lives
        self.level = 1
        self.extra_life_awarded = False
        bus.subscribe(DotEaten, lambda e: self.add_points(DOT_POINTS))
        bus.subscribe(EnergizerEaten, lambda e: self.add_points(ENERGIZER_POINTS))
        bus.subscribe(GhostEaten, lambda e: self.add_points(e.points))
        bus.subscribe(BonusEaten, lambda e: self.add_points(e.points))

    def add_points(self, points: int) -> None:
        self.score += points
        self.high_score = max(self.high_score, self.score)
        if not self.extra_life_awarded and self.score >= EXTRA_LIFE_SCORE:
            self.extra_life_awarded = True
            self.lives += 1
            self.bus.publish(ExtraLife(self.lives))

    def lose_life(self) -> bool:
        """Tira uma vida; devolve True se ainda restam vidas."""
        self.lives -= 1
        return self.lives > 0
