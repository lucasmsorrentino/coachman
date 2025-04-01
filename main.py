
from score_db import init_db
from Game import Game

if __name__ == "__main__":
    init_db()
    game = Game()
    game.run()
