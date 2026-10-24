# /// script
# dependencies = [
#   "pygame-ce",
# ]
# ///
"""Coach-Man -- ponto de entrada.

Computador:  python coachman/main.py
Navegador:   pygbag coachman   (ver README.md)

O bloco ``/// script`` acima (PEP 723) e o ``import pygame`` explícito avisam
o pygbag que ele precisa baixar o pygame-ce para o navegador. O
``asyncio.run(main())`` no fim também é exigido por ele: no navegador o laço
do jogo precisa devolver o controle ao browser a cada quadro.
"""
import asyncio
import sys
from pathlib import Path

import pygame  # noqa: F401  (ver docstring)

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from game.app import App  # noqa: E402


async def main() -> None:
    app = App(BASE_DIR)
    await app.run()


asyncio.run(main())
