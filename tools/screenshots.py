#!/usr/bin/env python3
"""Gera as imagens do README (``docs/img``) rodando o jogo sem janela.

    python tools/screenshots.py

Usa as cenas de verdade, com áudio nulo e placar em memória (os padrões Null
Object e Repository facilitam exatamente este tipo de automação).
"""
from __future__ import annotations

import os
import random
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "coachman"
sys.path.insert(0, str(GAME_DIR))

import pygame  # noqa: E402

from game.app import App  # noqa: E402
from game.config import DT  # noqa: E402
from game.core.audio import NullAudio  # noqa: E402
from game.persistence.highscores import InMemoryHighScoreRepository, ScoreEntry  # noqa: E402
from game.world.direction import Direction  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "img"
SCALE = 1


def save(app: App, name: str) -> None:
    app.render()
    OUT.mkdir(parents=True, exist_ok=True)
    big = pygame.transform.scale_by(app.screen, SCALE)
    pygame.image.save(big, str(OUT / f"{name}.png"))
    print("salvo", OUT / f"{name}.png")


def run_frames(app: App, frames: int, steer=None) -> None:
    for i in range(frames):
        if steer is not None:
            steer(i)
        app.update(DT)


def autopilot(scene, rng: random.Random):
    """Piloto simples: troca de direção de vez em quando."""

    def steer(i: int) -> None:
        if i % 12 == 0:
            scene.world.coachman.steer(rng.choice(list(Direction)))

    return steer


def bot(scene):
    """Piloto "esperto" para o GIF: busca em largura até o "$" mais próximo,
    evitando os tiles perto das cadeiras perigosas."""
    from collections import deque

    def steer(_i: int) -> None:
        world = scene.world
        maze = world.maze
        start = world.coachman.maze_tile
        danger = set()
        for g in world.ghosts:
            if world.is_deadly(g):
                gc, gr = g.maze_tile
                danger |= {(maze.wrap_col(gc + dc), gr + dr) for dc in (-2, -1, 0, 1, 2) for dr in (-2, -1, 0, 1, 2)}
        food = maze.dots | set(maze.energizers)
        queue, first = deque([start]), {start: None}
        while queue:
            c, r = queue.popleft()
            if (c, r) in food and (c, r) != start:
                step = (c, r)
                while first[step] is not None and first[step] != start:
                    step = first[step]
                for d in Direction:
                    if (maze.wrap_col(start[0] + d.dx), start[1] + d.dy) == step:
                        world.coachman.steer(d)
                return
            for d in Direction:
                n = (maze.wrap_col(c + d.dx), r + d.dy)
                if n not in first and maze.pacman_can_enter(*n) and n not in danger:
                    first[n] = (c, r)
                    queue.append(n)

    return steer


def record_gif(app: App, scene, name: str, seconds: float, every: int = 2) -> None:
    from PIL import Image

    frames = []
    steer = bot(scene)
    for i in range(int(seconds * 60)):
        steer(i)
        app.update(DT)
        if i % every == 0:
            app.render()
            raw = pygame.image.tobytes(app.screen, "RGB")
            frames.append(Image.frombytes("RGB", app.screen.get_size(), raw).quantize(64, dither=Image.Dither.NONE))
    OUT.mkdir(parents=True, exist_ok=True)
    frames[0].save(OUT / f"{name}.gif", save_all=True, append_images=frames[1:], duration=round(1000 * every / 60), loop=0,
                   optimize=True)
    print("salvo", OUT / f"{name}.gif", len(frames), "quadros")


def main() -> None:
    scores = InMemoryHighScoreRepository(
        [ScoreEntry("LMS", 18450, 4, "2026-10-24"), ScoreEntry("PAB", 9870, 2, "2026-10-24"),
         ScoreEntry("DAT", 4200, 1, "2026-10-24")]
    )
    app = App(GAME_DIR, audio=NullAudio(), scores=scores)

    from game.scenes.help import HelpScene
    from game.scenes.highscores import HighScoresScene
    from game.scenes.play import PlayScene
    from game.scenes.title import TitleScene

    app.scenes.push(TitleScene(app))
    save(app, "title")
    app.scenes.replace(HelpScene(app))
    run_frames(app, 20)
    save(app, "help")
    app.scenes.replace(HighScoresScene(app))
    save(app, "highscores")

    for level in (1, 2, 3):
        scene = PlayScene(app, start_level=level, seed=level)
        app.scenes.replace(scene)
        run_frames(app, 40)
        save(app, f"maze{level}_intro")
        run_frames(app, int(PlayScene.INTRO * 60))
        save(app, f"maze{level}_ready")

    scene = PlayScene(app, start_level=1, seed=11)
    app.scenes.replace(scene)
    run_frames(app, int((PlayScene.INTRO + PlayScene.READY) * 60) + 2)
    run_frames(app, 60 * 12, bot(scene))
    scene.debug = True
    save(app, "raio_x")
    scene.debug = False

    scene = PlayScene(app, start_level=1, seed=5)
    app.scenes.replace(scene)
    run_frames(app, int((PlayScene.INTRO + PlayScene.READY) * 60) + 2)
    record_gif(app, scene, "gameplay", 14)


if __name__ == "__main__":
    main()
