"""Relógio de modos, casa das cadeiras, sessão (placar/vidas) e tabela de fases."""
import pytest

from game.core.events import EventBus, ExtraLife
from game.levels import level_spec
from game.systems.mode_scheduler import CHASE, SCATTER, ModeScheduler
from game.systems.session import Session

DT = 1 / 60


def test_level_1_alternates_scatter_and_chase_like_the_arcade():
    modes = ModeScheduler(level_spec(1).mode_durations)
    assert modes.mode == SCATTER
    changes = []
    for frame in range(1, 60 * 60):
        if modes.update(DT):
            changes.append((frame, modes.mode))
    # dispersão 7 s, perseguição 20 s, dispersão 7 s, perseguição 20 s, dispersão 5 s...
    assert [m for _, m in changes] == [CHASE, SCATTER, CHASE, SCATTER, CHASE]
    expected = [7, 27, 34, 54, 59]
    for (frame, _), seconds in zip(changes, expected):
        assert frame == pytest.approx(seconds * 60, abs=1)


def test_fright_freezes_the_mode_clock():
    modes = ModeScheduler(level_spec(1).mode_durations)
    for _ in range(60):
        modes.update(DT)
    before = modes.elapsed
    modes.start_fright(6, 5)
    events = []
    for _ in range(6 * 60 + 1):
        events += modes.update(DT)
    assert events == ["fright_end"]
    assert modes.elapsed == pytest.approx(before)


def test_frightened_chairs_flash_only_at_the_end():
    modes = ModeScheduler(level_spec(1).mode_durations)
    modes.start_fright(6, 5)  # 5 piscadas de 0,4 s = últimos 2 s
    flashes = []
    for _ in range(6 * 60):
        flashes.append(modes.flashing)
        modes.update(DT)
    assert not any(flashes[: 4 * 60 - 2])
    assert any(flashes[4 * 60:])


def test_level_table_gets_harder():
    l1, l5, l21 = level_spec(1), level_spec(5), level_spec(21)
    assert (l1.pac_speed, l1.ghost_speed, l1.fright_time) == (0.80, 0.75, 6)
    assert l5.ghost_speed > l1.ghost_speed and l5.fright_time < l1.fright_time
    assert l21.fright_time == 0 and l21.bonus_points == 5000
    assert l1.dot_limits == {"pinky": 0, "inky": 30, "clyde": 60}


def test_house_releases_by_dot_counters(world):
    house = world.house
    pinky, inky, clyde = (world.by_name[n] for n in ("pinky", "inky", "clyde"))
    house.update(DT)
    assert pinky.state.name == "SAINDO"  # limite 0: sai na hora
    for _ in range(29):
        house.on_dot_eaten()
        house.update(DT)
    assert inky.state.name == "NA CASA"
    house.on_dot_eaten()
    house.update(DT)
    assert inky.state.name == "SAINDO"  # 30 bolinhas
    assert clyde.state.name == "NA CASA"


def test_house_releases_when_player_stops_eating(world):
    house = world.house
    house.update(DT)  # Pinky sai
    inky = world.by_name["inky"]
    for _ in range(int(4 * 60) - 5):
        house.update(DT)
    assert inky.state.name == "NA CASA"
    for _ in range(10):
        house.update(DT)
    assert inky.state.name == "SAINDO"


def test_global_counter_after_losing_a_life(world):
    house = world.house
    house.on_life_lost()
    pinky, inky = world.by_name["pinky"], world.by_name["inky"]
    for _ in range(6):
        house.on_dot_eaten()
    assert pinky.state.name == "NA CASA"
    house.on_dot_eaten()  # 7
    assert pinky.state.name == "SAINDO"
    for _ in range(10):
        house.on_dot_eaten()  # 17
    assert inky.state.name == "SAINDO"


def test_extra_life_at_10000_points_only_once():
    bus = EventBus()
    lives = []
    bus.subscribe(ExtraLife, lives.append)
    session = Session(bus)
    session.add_points(9990)
    assert session.lives == 3
    session.add_points(20)
    session.add_points(20000)
    assert session.lives == 4 and len(lives) == 1
    assert session.high_score == 30010
