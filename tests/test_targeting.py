"""As quatro personalidades (Strategy) calculam o alvo como no arcade."""
from game.actors import targeting
from game.actors.targeting import (
    AmbushTargeting,
    PokeyTargeting,
    ShadowTargeting,
    TargetContext,
    WhimsicalTargeting,
    tiles_ahead,
)
from game.world.direction import Direction


def ctx(pac=(10, 10), direction=Direction.LEFT, ghost=(0, 0), blinky=(0, 0), scatter=(0, 32)):
    return TargetContext(pac, direction, ghost, blinky, scatter)


def test_blinky_targets_pacman_tile():
    assert ShadowTargeting().chase_target(ctx(pac=(7, 20))) == (7, 20)


def test_pinky_targets_four_tiles_ahead():
    assert AmbushTargeting().chase_target(ctx(direction=Direction.LEFT)) == (6, 10)
    assert AmbushTargeting().chase_target(ctx(direction=Direction.RIGHT)) == (14, 10)
    assert AmbushTargeting().chase_target(ctx(direction=Direction.DOWN)) == (10, 14)


def test_pinky_reproduces_arcade_overflow_bug_when_facing_up():
    # olhando para cima, o arcade também desloca 4 tiles para a esquerda
    assert AmbushTargeting().chase_target(ctx(direction=Direction.UP)) == (6, 6)


def test_overflow_bug_can_be_disabled(monkeypatch):
    monkeypatch.setattr(targeting, "REPRODUCE_ARCADE_OVERFLOW_BUG", False)
    assert tiles_ahead((10, 10), Direction.UP, 4) == (10, 6)


def test_inky_doubles_vector_from_blinky_to_pivot():
    # pivô = 2 tiles à direita do Coach-Man = (12, 10); Blinky em (8, 6)
    # alvo = pivô + (pivô - Blinky) = (16, 14)
    target = WhimsicalTargeting().chase_target(ctx(direction=Direction.RIGHT, blinky=(8, 6)))
    assert target == (16, 14)


def test_clyde_chases_when_far_and_retreats_when_close():
    clyde = PokeyTargeting()
    far = ctx(pac=(10, 10), ghost=(10, 18), scatter=(0, 32))  # distância 8 -> persegue
    near = ctx(pac=(10, 10), ghost=(10, 17), scatter=(0, 32))  # distância 7 -> canto
    assert clyde.chase_target(far) == (10, 10)
    assert clyde.chase_target(near) == (0, 32)
