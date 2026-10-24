"""Os labirintos seguem as regras de um bom labirinto de Pac-Man."""
import pytest

from game.world.maze import Maze, MazeDefinition, validate
from game.world.maze_data import DEBATE, MAZES, maze_for_level


@pytest.mark.parametrize("definition", MAZES, ids=lambda d: d.name)
def test_maze_is_valid(definition):
    assert validate(definition) == []


def test_classic_maze_has_the_arcade_food_count():
    maze = Maze.from_definition(DEBATE)
    assert len(maze.dots) == 240 and len(maze.energizers) == 4


def test_tunnels_are_detected():
    maze = Maze.from_definition(DEBATE)
    assert maze.is_tunnel(0, 14) and maze.is_tunnel(27, 14)
    assert not maze.is_tunnel(6, 14)
    assert not maze.is_wall(-1, 14)  # o túnel "dá a volta"


def test_levels_cycle_through_the_mazes():
    assert [maze_for_level(n).name for n in (1, 2, 3, 4)] == [m.name for m in MAZES] + [MAZES[0].name]


def test_validator_catches_dead_ends():
    rows = list(DEBATE.layout)
    rows[1] = rows[1][:6] + "#" + rows[1][7:21] + "#" + rows[1][22:]  # fecha um corredor
    broken = MazeDefinition("QUEBRADO", "", tuple(rows), (0, 0, 255))
    assert any("beco" in p for p in validate(broken))


def test_house_geometry():
    maze = Maze.from_definition(DEBATE)
    assert maze.house_exit_tiles == {(13, 11), (14, 11)}
    assert maze.house_center_x == 14 * 16
