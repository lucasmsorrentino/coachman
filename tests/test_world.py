"""Regras de uma fase: comer, power-up, devorar cadeiras, morrer, vovó, fim de fase."""
import random

from conftest import center, record
from game.actors import ghost_states as gs
from game.config import DOT_PAUSE, ENERGIZER_PAUSE
from game.core.events import (
    BonusSpawned,
    CoachManCaught,
    DotEaten,
    EnergizerEaten,
    GhostEaten,
    LevelCleared,
)
from game.systems.session import Session
from game.world.direction import Direction
from game.world.maze_data import MAZES
from game.world.world import World


def test_eating_a_dollar_scores_10_and_pauses_one_frame(world, bus):
    session = Session(bus)
    log = record(bus, DotEaten)
    pac = world.coachman
    pac.place(*center(12, 23), Direction.LEFT)
    world.update(1 / 60)
    assert log and session.score == 10
    assert pac.freeze == DOT_PAUSE


def test_energizer_frightens_the_chairs(world, bus):
    log = record(bus, EnergizerEaten)
    blinky = world.by_name["blinky"]
    world.coachman.place(*center(1, 4), Direction.UP)  # (1, 3) é power-up
    for _ in range(10):
        world.update(1 / 60)
        if log:
            break
    assert log
    assert world.coachman.freeze == ENERGIZER_PAUSE
    assert blinky.state is gs.FRIGHTENED and blinky.frightened
    assert world.modes.frightened
    assert world.by_name["clyde"].frightened  # até quem está na casa fica azul


def test_fright_makes_roaming_chairs_turn_around(world):
    blinky = world.by_name["blinky"]
    blinky.place(*center(8, 5), Direction.RIGHT)
    blinky.change_state(gs.CHASE)
    world._start_fright()
    assert blinky.direction is Direction.LEFT


def test_energizer_icons_are_four_different_logos():
    icons = list(World(1, __import__("game.core.events", fromlist=["EventBus"]).EventBus(),
                       random.Random(4)).maze.energizers.values())
    assert len(icons) == 4 and len(set(icons)) == 4
    assert all(0 <= i < 7 for i in icons)


def test_eating_chairs_doubles_the_points(world, bus):
    session = Session(bus)
    log = record(bus, GhostEaten)
    world._start_fright()
    pac = world.coachman
    for name in ("blinky", "pinky", "inky", "clyde"):
        ghost = world.by_name[name]
        ghost.place(pac.x, pac.y, Direction.LEFT)
        ghost.change_state(gs.FRIGHTENED)
        ghost.frightened = True
        assert world._check_collisions()
        world.pause_frames = 0
    assert [e.points for e in log] == [200, 400, 800, 1600]
    assert session.score == 3000
    assert all(g.state is gs.EATEN for g in world.ghosts)


def test_touching_a_chasing_chair_is_fatal(world, bus):
    log = record(bus, CoachManCaught)
    blinky = world.by_name["blinky"]
    blinky.place(world.coachman.x, world.coachman.y, Direction.LEFT)
    world.update(1 / 60)
    assert world.caught_by is blinky and log


def test_restart_after_death_keeps_eaten_dots(world):
    world.coachman.place(*center(12, 23), Direction.LEFT)
    world.update(1 / 60)
    left = world.maze.food_left
    world.restart_after_death()
    assert world.maze.food_left == left
    assert world.house.use_global and world.elroy_suspended
    assert world.by_name["pinky"].state is gs.IN_HOUSE


def test_bonus_appears_after_70_dots(world, bus):
    log = record(bus, BonusSpawned)
    for tile in sorted(world.maze.dots)[:70]:
        world._eat(tile)
    assert log and world.bonus.active
    assert 9 <= world.bonus.time_left <= 10


def test_blinky_becomes_cruise_elroy_near_the_end(world):
    blinky = world.by_name["blinky"]
    assert world.elroy_level(blinky) == 0
    for tile in sorted(world.maze.dots)[: world.maze.food_left - 20]:
        world._eat(tile)
    assert world.elroy_level(blinky) == 1
    assert world.ghost_speed(blinky) == world.spec.elroy1_speed


def test_level_is_cleared_when_all_food_is_eaten(world, bus):
    log = record(bus, LevelCleared)
    for tile in list(world.maze.dots) + list(world.maze.energizers):
        world._eat(tile)
    world.pause_frames = 0
    world.modes.fright_left = 0
    world.coachman.place(*center(6, 23), Direction.LEFT)
    for g in world.ghosts:
        g.place(*center(26, 1), Direction.LEFT)
    world.update(1 / 60)
    assert world.cleared and log


def test_every_maze_plays_without_errors():
    for level in range(1, len(MAZES) + 1):
        w = World(level, __import__("game.core.events", fromlist=["EventBus"]).EventBus(), random.Random(level))
        rng = random.Random(level)
        for frame in range(60 * 40):
            if frame % 10 == 0:
                w.coachman.steer(rng.choice(list(Direction)))
            w.update(1 / 60)
            if w.caught_by:
                w.restart_after_death()
            assert not w.maze.is_wall(*w.coachman.maze_tile)
