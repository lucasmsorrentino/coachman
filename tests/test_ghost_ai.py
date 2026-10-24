"""Navegação e estados das cadeiras (State + regras do arcade)."""
from conftest import center
from game.actors import ghost_states as gs
from game.actors.ghost_states import choose_random, choose_toward
from game.world.direction import Direction


def blinky(world):
    return world.by_name["blinky"]


def test_picks_exit_closest_to_target_in_straight_line(world):
    g = blinky(world)
    g.place(*center(6, 5), Direction.RIGHT)  # cruzamento com 4 saídas
    assert choose_toward(g, (6, 0)) is Direction.UP
    assert choose_toward(g, (6, 30)) is Direction.DOWN
    assert choose_toward(g, (27, 5)) is Direction.RIGHT


def test_never_reverses_on_its_own(world):
    g = blinky(world)
    g.place(*center(6, 5), Direction.RIGHT)
    # o alvo está atrás (à esquerda), mas voltar não é permitido
    assert choose_toward(g, (0, 5)) is not Direction.LEFT


def test_ties_are_broken_up_left_down_right(world):
    g = blinky(world)
    g.place(*center(6, 5), Direction.RIGHT)
    # vizinho de cima (6,4) e da direita (7,5) estão à mesma distância de (7,4)
    assert choose_toward(g, (7, 4)) is Direction.UP


def test_no_up_tiles_above_the_house(world):
    g = blinky(world)
    g.place(*center(12, 11), Direction.RIGHT)
    assert (12, 11) in world.maze.definition.no_up_tiles
    assert choose_toward(g, (12, 0)) is not Direction.UP
    assert choose_toward(g, (12, 0), restrict_up=False) is Direction.UP


def test_frightened_choice_is_random_but_never_reverses(world):
    g = blinky(world)
    g.place(*center(6, 5), Direction.RIGHT)
    picks = {choose_random(g) for _ in range(200)}
    assert Direction.LEFT not in picks
    assert picks == {Direction.UP, Direction.DOWN, Direction.RIGHT}


def test_ghosts_never_enter_walls_during_a_long_game(world):
    pac = world.coachman
    for frame in range(60 * 60):
        if frame % 15 == 0:
            pac.steer(list(Direction)[(frame // 15) % 4])
        world.update(1 / 60)
        if world.caught_by:
            world.restart_after_death()
        for g in world.ghosts:
            if not g.in_house:
                assert g.maze_tile not in world.maze.walls, g


def test_pinky_leaves_the_house_and_starts_roaming(world):
    pinky = world.by_name["pinky"]
    assert pinky.state is gs.IN_HOUSE
    for _ in range(240):
        world.update(1 / 60)
    assert pinky.state in (gs.SCATTER, gs.CHASE)
    assert pinky.tile[1] <= 11


def test_eaten_ghost_flies_home_and_comes_back(world):
    g = blinky(world)
    g.place(*center(6, 5), Direction.RIGHT)
    g.change_state(gs.EATEN)
    seen = set()
    for _ in range(60 * 10):
        g.update()
        seen.add(g.state)
        if g.state in (gs.SCATTER, gs.CHASE):
            break
    assert gs.ENTERING_HOUSE in seen and gs.LEAVING_HOUSE in seen
    assert g.state in (gs.SCATTER, gs.CHASE)
    assert not g.frightened


def test_scatter_targets_are_the_four_corners(world):
    corners = {g.name: g.scatter_tile for g in world.ghosts}
    assert corners == {"blinky": (25, -3), "pinky": (2, -3), "inky": (27, 32), "clyde": (0, 32)}
