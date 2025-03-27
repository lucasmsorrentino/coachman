import pygame
import Engine
from constants import *
from Entity import Coachman, Ghost, Maze
from EntityFactory import Factory
from Menu import Menu
from Engine import Engine


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.init()

        


    def run(self):
        pygame.mixer.init()
        while True:
            menu = Menu(self.screen)
            menu_return = menu.run()

            if menu_return == MENU_OPTION[1]:  # Scores
                pass
            elif menu_return == MENU_OPTION[2]:  # Exit
                pygame.quit()
                return
            elif menu_return == MENU_OPTION[0]:  # Play
                engine = Engine()
                engine.run_game_loop()
