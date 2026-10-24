"""Movimento do Coach-Man: paredes, curva antecipada, meia-volta, túnel."""
import pytest

from conftest import center
from game.config import BASE_SPEED, TILE
from game.world.direction import Direction


def run(actor, frames):
    for _ in range(frames):
        actor.update()


def test_starts_between_tiles_and_moves_left_at_level_speed(world):
    pac = world.coachman
    assert (pac.x, pac.y) == (14 * TILE, 23.5 * TILE)
    x0 = pac.x
    pac.update()
    assert pac.x == pytest.approx(x0 - 0.80 * BASE_SPEED)


def test_stops_at_the_center_of_the_tile_before_a_wall(world):
    pac = world.coachman
    pac.place(*center(7, 23), Direction.LEFT)  # (5, 23) é parede
    run(pac, 30)
    assert (pac.x, pac.y) == center(6, 23)
    assert pac.moved == 0


def test_reverses_instantly(world):
    pac = world.coachman
    pac.place(*center(10, 23), Direction.LEFT)
    pac.x -= 3
    pac.steer(Direction.RIGHT)
    pac.update()
    assert pac.direction is Direction.RIGHT


def test_cornering_turns_before_reaching_the_center(world):
    pac = world.coachman
    cx, cy = center(12, 23)  # (12, 22) é corredor: dá para subir
    pac.place(cx + 5, cy, Direction.LEFT)
    pac.steer(Direction.UP)
    pac.update()
    assert pac.direction is Direction.UP
    assert pac.y < cy  # já subiu...
    assert cx < pac.x < cx + 5  # ...enquanto se alinhava ao centro (diagonal)
    run(pac, 5)
    assert pac.x == cx  # alinhado


def test_buffered_turn_is_taken_at_the_next_opening(world):
    pac = world.coachman
    pac.place(*center(9, 23), Direction.LEFT)  # (9, 22) é parede; (6, 22) não
    pac.steer(Direction.UP)
    run(pac, 25)
    assert pac.direction is Direction.UP
    assert pac.tile[0] == 6


def test_cannot_enter_the_ghost_house_door(world):
    pac = world.coachman
    pac.place(*center(13, 11), Direction.LEFT)
    pac.steer(Direction.DOWN)  # (13, 12) é a porta
    run(pac, 10)
    assert pac.tile[1] == 11


def test_tunnel_wraps_to_the_other_side(world):
    pac = world.coachman
    pac.place(*center(1, 14), Direction.LEFT)
    run(pac, 40)
    assert pac.x > 20 * TILE
    assert pac.direction is Direction.LEFT


def test_animation_only_advances_while_moving(world):
    pac = world.coachman
    pac.place(*center(6, 23), Direction.LEFT)
    run(pac, 5)
    frame = pac.anim_frame
    run(pac, 20)
    assert pac.anim_frame == frame
