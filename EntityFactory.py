import pygame
import random
from constants import *
from GameEngine import Pacman, Ghost


class Factory:
    def __init__(self, maze):
        self.maze = maze
        
    def create_pacman(self):
        pos = self.maze.find_initial_pos(4)
        return Pacman(self.maze, pos)
    
    def create_ghost(self):
        pos = self.maze.find_initial_pos(3)
        return Ghost(self.maze, pos)
