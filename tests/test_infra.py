"""Infraestrutura: eventos, comandos, repositórios de recorde e cenas."""
import pygame
import pytest

from game.core.commands import CONFIRM, DOWN, LEFT, MUTE, PAUSE, UP, CommandTarget, InputHandler, TextCommand
from game.core.events import DotEaten, EventBus
from game.persistence.highscores import (
    BrowserHighScoreRepository,
    InMemoryHighScoreRepository,
    ScoreEntry,
    SqliteHighScoreRepository,
)
from game.world.direction import Direction


# ---------------------------------------------------------------- Observer
def test_event_bus_delivers_by_type_and_unsubscribes():
    bus = EventBus()
    got = []
    off = bus.subscribe(DotEaten, got.append)
    bus.publish(DotEaten((1, 1), 10))
    bus.publish("outro tipo")
    off()
    bus.publish(DotEaten((2, 2), 9))
    assert len(got) == 1


# ---------------------------------------------------------------- Command
def key(k, unicode=""):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=unicode, mod=0)


def test_keyboard_maps_to_commands():
    handler = InputHandler()
    assert handler.translate(key(pygame.K_UP)) == [UP]
    assert handler.translate(key(pygame.K_a)) == [LEFT]
    assert handler.translate(key(pygame.K_RETURN)) == [CONFIRM]
    assert handler.translate(key(pygame.K_m)) == [MUTE]


def test_text_mode_types_letters_instead_of_shortcuts():
    handler = InputHandler()
    handler.text_mode = True
    [command] = handler.translate(key(pygame.K_m, "m"))
    assert isinstance(command, TextCommand) and command.char == "M"


def test_swipe_and_tap():
    handler = InputHandler()
    down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(100, 100), button=1)
    move = pygame.event.Event(pygame.MOUSEMOTION, pos=(100, 140), rel=(0, 40), buttons=(1, 0, 0))
    up = pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(100, 140), button=1)
    further = pygame.event.Event(pygame.MOUSEMOTION, pos=(100, 190), rel=(0, 50), buttons=(1, 0, 0))
    assert handler.translate(down) == []
    assert handler.translate(move) == [DOWN]
    assert handler.translate(further) == []  # mesmo gesto, mesma direção: um comando só
    assert handler.translate(up) == []  # foi deslize, não toque
    handler.translate(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(10, 100), button=1))
    assert handler.translate(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(12, 101), button=1)) == [CONFIRM]
    handler.translate(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(440, 10), button=1))
    assert handler.translate(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(440, 10), button=1)) == [PAUSE]


def test_commands_execute_on_any_target():
    class Target(CommandTarget):
        def __init__(self):
            self.moves = []

        def on_direction(self, direction):
            self.moves.append(direction)

    target = Target()
    UP.execute(target)
    CONFIRM.execute(target)  # ignorado: CommandTarget tem implementação vazia
    assert target.moves == [Direction.UP]


# ---------------------------------------------------------------- Repository
class FakeLocalStorage:
    def __init__(self):
        self.data = {}

    def getItem(self, key):
        return self.data.get(key)

    def setItem(self, key, value):
        self.data[key] = value


@pytest.fixture(params=["memory", "sqlite", "browser"])
def repo(request, tmp_path):
    if request.param == "memory":
        return InMemoryHighScoreRepository()
    if request.param == "sqlite":
        return SqliteHighScoreRepository(tmp_path / "scores.db")
    return BrowserHighScoreRepository(FakeLocalStorage())


def test_repositories_keep_the_top_10_sorted(repo):
    for i in range(12):
        repo.add(ScoreEntry.new("abc", i * 100, 1))
    top = repo.top()
    assert len(top) == 10
    assert [e.score for e in top] == sorted((e.score for e in top), reverse=True)
    assert repo.best() == 1100
    assert repo.qualifies(5000) and not repo.qualifies(150)
    assert top[0].initials == "ABC"


def test_initials_are_sanitized():
    assert ScoreEntry.new("a!b?c?d", 10, 1).initials == "ABC"
    assert ScoreEntry.new("", 10, 1).initials == "???"


# ---------------------------------------------------------------- cenas (fumaça)
def test_scenes_flow_without_errors(tmp_path):
    from pathlib import Path

    from game.app import App
    from game.core.audio import NullAudio
    from game.scenes.play import Phase, PlayScene
    from game.scenes.title import TitleScene

    base = Path(__file__).resolve().parents[1] / "coachman"
    audio = NullAudio()
    app = App(base, audio=audio, scores=InMemoryHighScoreRepository())
    app.scenes.push(TitleScene(app))
    for _ in range(3):
        DOWN.execute(app.scenes.top)
    UP.execute(app.scenes.top)
    UP.execute(app.scenes.top)
    UP.execute(app.scenes.top)  # volta para ">Play<"
    CONFIRM.execute(app.scenes.top)
    play = app.scenes.top
    assert isinstance(play, PlayScene)
    for frame in range(60 * 20):
        if frame % 20 == 0:
            play.on_direction(list(Direction)[frame // 20 % 4])
        app.update(1 / 60)
        app.render()
    assert play.phase in set(Phase)
    play.on_pause()
    assert len(app.scenes) == 2
    CONFIRM.execute(app.scenes.top)
    assert app.scenes.top is play
    assert "music:gameplay" in audio.played


def test_game_over_leads_to_initials_and_high_scores():
    from pathlib import Path

    from game.app import App
    from game.core.audio import NullAudio
    from game.core.commands import RIGHT, TextCommand
    from game.scenes.gameover import GameOverScene
    from game.scenes.highscores import HighScoresScene
    from game.scenes.initials import InitialsScene
    from game.scenes.play import Phase, PlayScene

    base = Path(__file__).resolve().parents[1] / "coachman"
    scores = InMemoryHighScoreRepository()
    app = App(base, audio=NullAudio(), scores=scores)
    play = PlayScene(app, seed=1)
    app.scenes.push(play)
    play.session.score = 4321
    play.session.lives = 1
    play._set_phase(Phase.DYING, 0.01)
    for _ in range(3):
        app.update(1 / 60)
    assert play.phase is Phase.GAME_OVER
    for _ in range(int(PlayScene.GAME_OVER_TIME * 60) + 2):
        app.update(1 / 60)
    assert isinstance(app.scenes.top, GameOverScene)
    for _ in range(int(GameOverScene.DURATION * 60) + 2):
        app.update(1 / 60)
    initials = app.scenes.top
    assert isinstance(initials, InitialsScene)
    for ch in "LMS":
        TextCommand(ch).execute(initials)
    RIGHT.execute(initials)
    CONFIRM.execute(initials)
    assert isinstance(app.scenes.top, HighScoresScene)
    assert scores.top()[0].initials == "LMS" and scores.top()[0].score == 4321
    app.render()
