import pygame
import random
from constants import *
from Entity import Coachman, Ghost

class Factory:
    def __init__(self, maze):
        self.maze = maze
        
    def create_coachman(self):
        pos = self.maze.find_initial_pos(4)
        return Coachman(self.maze, pos)
    
    def create_ghosts(self, count=4):
        # Get all ghost spawn positions
        ghost_spawn_positions = self.maze.find_all_initial_pos(3)
        if not ghost_spawn_positions:
            # Fallback if no spawn positions are found
            ghost_spawn_positions = [(1,1)]
        # Ensure there are enough spawn positions (repeat if necessary)
        while len(ghost_spawn_positions) < count:
            ghost_spawn_positions *= 2
        # Shuffle and assign unique positions
        random.shuffle(ghost_spawn_positions)
        
        # Define the ghost types in the order you want
        ghost_types = ["BLINKY", "PINKY", "INKY", "CLYDE"]
        ghosts = []
        for i in range(count):
            pos = ghost_spawn_positions[i]
            ghost = Ghost(self.maze, pos)
            # Assign a specific type instead of a random one
            ghost.type = ghost_types[i % len(ghost_types)]
            ghosts.append(ghost)
        return ghosts


    # Optionally, keep the old create_ghost for backward compatibility.
   # def create_ghost(self):
    #    pos = self.maze.find_initial_pos(3)
     #   return Ghost(self.maze, pos)

