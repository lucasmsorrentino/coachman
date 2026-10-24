"""Quando cada cadeira sai da casa (regras do arcade).

Blinky já começa do lado de fora. As outras saem na ordem Pinky -> Inky ->
Clyde, controladas por **contadores de "$"**:

* Cada cadeira tem um limite por fase (fase 1: Pinky 0, Inky 30, Clyde 60;
  fase 2: 0, 0, 50; depois: 0, 0, 0). Só o contador da *primeira cadeira da
  fila* avança quando o Coach-Man come um "$".
* Depois que o Coach-Man morre, passa a valer um **contador global**: Pinky
  sai com 7 "$", Inky com 17 e Clyde com 32.
* **Anti-acampamento**: se o jogador ficar 4 s (3 s a partir da fase 5) sem
  comer nada, a próxima cadeira da fila é liberada à força.

Fonte: The Pac-Man Dossier, seção "Home Sweet Home".
"""
from __future__ import annotations

from typing import Iterable

from ..actors.ghost import Ghost
from ..actors.ghost_states import IN_HOUSE
from ..levels import LevelSpec

GLOBAL_LIMITS = {"pinky": 7, "inky": 17, "clyde": 32}
QUEUE = ("pinky", "inky", "clyde")


class GhostHouse:
    def __init__(self, spec: LevelSpec, ghosts: Iterable[Ghost]) -> None:
        self.spec = spec
        self.ghosts = {g.name: g for g in ghosts}
        self.counters = {name: 0 for name in QUEUE}
        self.use_global = False
        self.global_counter = 0
        self.idle = 0.0

    def preferred(self) -> Ghost | None:
        for name in QUEUE:
            ghost = self.ghosts.get(name)
            if ghost is not None and ghost.state is IN_HOUSE:
                return ghost
        return None

    def on_life_lost(self) -> None:
        self.use_global = True
        self.global_counter = 0
        self.idle = 0.0

    def on_dot_eaten(self) -> None:
        self.idle = 0.0
        if self.use_global:
            self.global_counter += 1
            for name, limit in GLOBAL_LIMITS.items():
                ghost = self.ghosts.get(name)
                if self.global_counter == limit and ghost is not None and ghost.state is IN_HOUSE:
                    if name == "clyde":
                        self.use_global = False  # volta aos contadores individuais
                    ghost.release()
            return
        ghost = self.preferred()
        if ghost is not None:
            self.counters[ghost.name] += 1

    def update(self, dt: float) -> None:
        ghost = self.preferred()
        if ghost is None:
            return
        if not self.use_global and self.counters[ghost.name] >= self.spec.dot_limits[ghost.name]:
            ghost.release()
            return
        self.idle += dt
        if self.idle >= self.spec.house_idle_limit:
            self.idle = 0.0
            ghost.release()
