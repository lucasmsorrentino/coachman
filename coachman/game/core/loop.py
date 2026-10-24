"""Laço principal -- padrão **Game Loop** com passo fixo.

A simulação sempre avança em passos de exatamente 1/60 s (como o arcade,
que roda a 60 quadros por segundo), não importa a velocidade do computador.
O tempo real que passou é acumulado e "gasto" em passos fixos; a renderização
acontece uma vez por volta do laço. Isso deixa o jogo determinístico (os
testes reproduzem partidas quadro a quadro) e evita que um computador lento
deixe o Coach-Man atravessar paredes.

O laço é ``async`` porque no navegador (pygbag/WebAssembly) é preciso
devolver o controle ao browser a cada quadro (``await asyncio.sleep(0)``).

Referência: Robert Nystrom, *Game Programming Patterns*,
https://gameprogrammingpatterns.com/game-loop.html
"""
from __future__ import annotations

import asyncio
import time
from typing import Callable

MAX_FRAME_TIME = 0.25  # evita a "espiral da morte" após uma pausa longa


class GameLoop:
    def __init__(
        self,
        step: float,
        process_input: Callable[[], None],
        update: Callable[[float], None],
        render: Callable[[], None],
        tick: Callable[[], None] | None = None,
    ) -> None:
        self.step = step
        self.process_input = process_input
        self.update = update
        self.render = render
        self.tick = tick or (lambda: None)
        self.running = False

    async def run(self) -> None:
        self.running = True
        previous = time.perf_counter()
        lag = 0.0
        while self.running:
            now = time.perf_counter()
            lag += min(now - previous, MAX_FRAME_TIME)
            previous = now

            self.process_input()
            while lag >= self.step and self.running:
                self.update(self.step)
                lag -= self.step
            self.render()
            self.tick()
            await asyncio.sleep(0)

    def stop(self) -> None:
        self.running = False
