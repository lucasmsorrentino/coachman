import os
import random

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from game.config import TILE  # noqa: E402
from game.core.events import EventBus  # noqa: E402
from game.world.world import World  # noqa: E402


@pytest.fixture
def bus():
    return EventBus()


@pytest.fixture
def world(bus):
    return World(1, bus, random.Random(1))


def center(col, row):
    """Centro do tile em pixels."""
    return (col + 0.5) * TILE, (row + 0.5) * TILE


def record(bus, *event_types):
    """Assina os eventos e devolve a lista onde eles serão gravados."""
    log = []
    for et in event_types:
        bus.subscribe(et, log.append)
    return log
