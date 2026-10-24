"""Relógio global dos modos das cadeiras.

No arcade as cadeiras NÃO perseguem o tempo todo. Um cronômetro alterna:

    dispersão 7s -> perseguição 20s -> dispersão 7s -> perseguição 20s
    -> dispersão 5s -> perseguição 20s -> dispersão 5s -> perseguição para sempre

(tempos da fase 1; ver ``levels.py``). As "pausas" de dispersão são o que
dá respiro ao jogador. Durante o modo assustado esse cronômetro fica
**congelado** e só volta a contar quando o susto acaba.
"""
from __future__ import annotations

SCATTER, CHASE = "scatter", "chase"
FLASH_PERIOD = 0.4  # s: um "pisca" (branco + azul) no fim do susto


class ModeScheduler:
    def __init__(self, durations: tuple[float, ...]) -> None:
        self.durations = durations
        self.index = 0
        self.elapsed = 0.0
        self.fright_left = 0.0
        self.fright_total = 0.0
        self.fright_flashes = 0

    @property
    def mode(self) -> str:
        return SCATTER if self.index % 2 == 0 else CHASE

    @property
    def time_left(self) -> float:
        return self.durations[self.index] - self.elapsed

    @property
    def frightened(self) -> bool:
        return self.fright_left > 0

    @property
    def flashing(self) -> bool:
        """True quando a cadeira deve aparecer branca neste instante."""
        if not self.frightened or self.fright_flashes == 0:
            return False
        flash_window = self.fright_flashes * FLASH_PERIOD
        if self.fright_left > flash_window:
            return False
        phase = (flash_window - self.fright_left) % FLASH_PERIOD
        return phase < FLASH_PERIOD / 2

    def start_fright(self, seconds: float, flashes: int) -> None:
        self.fright_left = self.fright_total = seconds
        self.fright_flashes = flashes

    def update(self, dt: float) -> list[str]:
        """Avança o relógio; devolve os eventos ocorridos ("mode", "fright_end")."""
        events = []
        if self.fright_left > 0:
            self.fright_left -= dt
            if self.fright_left <= 0:
                self.fright_left = 0
                events.append("fright_end")
            return events  # cronômetro de modos congelado durante o susto
        self.elapsed += dt
        while self.index < len(self.durations) - 1 and self.elapsed >= self.durations[self.index]:
            self.elapsed -= self.durations[self.index]
            self.index += 1
            events.append("mode")
        return events
