
from dataclasses import dataclass
from typing import List, Set, Tuple
import pygame
import random
from constants import *



class Entity:
    def __init__(self, maze, position):
        self.maze = maze
        self.position = position
        self.direction = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])


class Coachman:
    def __init__(self, maze, position):
        self.maze = maze
        self.position = position
        self.score = 0
        self.lives = 3
        self.direction = "Down"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.maze.grid[self.position[0]][self.position[1]] = 4

    def move(self, direction):
        row, col = self.position
        new_row, new_col = row, col
        
        if direction == "UP":
            new_row -= 1
        elif direction == "DOWN":
            new_row += 1
        elif direction == "LEFT":
            new_col -= 1
        elif direction == "RIGHT":
            new_col += 1
        
        if self.maze.is_valid_move(new_row, new_col):
            if (new_row, new_col) in self.maze.pellets:
                self.maze.pellets.remove((new_row, new_col))
                self.score += 10
            
            self.maze.update_position((row, col), (new_row, new_col), 4)
            self.position = [new_row, new_col]
            # Match asset filename spelling exactly ("Righ" instead of "Right")
            self.direction = "Righ" if direction.upper() == "RIGHT" else direction.capitalize()
            # Advance animation frame
            self.current_frame = (self.current_frame + 1) % COACHMAN_FRAMES_PER_DIR
            
    def reset_position(self):
        self.position = self.maze.find_initial_pos(4)
        self.maze.grid[self.position[0]][self.position[1]] = 4

class Ghost:
    def __init__(self, maze, position):
        self.maze = maze
        self.position = position
        self.directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        self.maze.grid[self.position[0]][self.position[1]] = 3

    def move(self):
        row, col = self.position
        random.shuffle(self.directions)
        
        for dr, dc in self.directions:
            new_row, new_col = row + dr, col + dc
            
            if self.maze.is_valid_move(new_row, new_col):
                self.maze.update_position((row, col), (new_row, new_col), 3)
                self.position = [new_row, new_col]
                break
                
    def reset_position(self):
        self.position = self.maze.find_initial_pos(3)
        self.maze.grid[self.position[0]][self.position[1]] = 3



@dataclass
class Maze:
    def all_pellets_collected(self):
        return len(self.pellets) == 0

    grid: List[List[int]]
    pellets: Set[Tuple[int, int]]


    
    def __init__(self):
        self.pellets = {
            (r, c) for r, row in enumerate(INITIAL_GRID)
            for c, val in enumerate(row) if val == 2
        }
        self.grid = [row[:] for row in INITIAL_GRID]
        self.coachman_sprites = {}
        self.coachman = None

    def reset(self):
        """Reset maze to initial state while preserving sprites and coachman reference"""
        self.pellets = {
            (r, c) for r, row in enumerate(INITIAL_GRID)
            for c, val in enumerate(row) if val == 2
        }
        self.grid = [row[:] for row in INITIAL_GRID]

    def load_coachman_sprites(self):
        self.coachman_sprites = {
            dir: [
                pygame.image.load(f"asset/coachMan{dir}0{i}.png") 
                for i in range(1,4)
            ]
            for dir in ["Up", "Down", "Left", "Righ"]  # Fixed typo to match asset filenames
        }
        # Scale all sprites to GRID_SIZE
        for dir in self.coachman_sprites:
            self.coachman_sprites[dir] = [
                pygame.transform.scale(img, (GRID_SIZE, GRID_SIZE))
                for img in self.coachman_sprites[dir]
            ]

    def __getitem__(self, idx):
        return self.grid[idx[0]][idx[1]]
        
    def __setitem__(self, idx, value):
        r, c = idx
        if self.grid[r][c] == 2:
            self.pellets.discard((r, c))
        if value == 2:
            self.pellets.add((r, c))
        self.grid[r][c] = value

    def find_initial_pos(self, entity_type):
        return next(
            ((r, c) for r, row in enumerate(self.grid)
             for c, val in enumerate(row) if val == entity_type),
            (1, 1)  # default
        )

    def draw(self, screen):
        draw_map = {
            1: lambda x,y: pygame.draw.rect(screen, BLUE, (x, y, GRID_SIZE, GRID_SIZE)),
            2: lambda x,y: pygame.draw.circle(screen, WHITE, (x + GRID_SIZE//2, y + GRID_SIZE//2), 5),
            3: lambda x,y: pygame.draw.circle(screen, RED, (x + GRID_SIZE//2, y + GRID_SIZE//2), 12),
            4: lambda x,y: screen.blit(
                self.coachman_sprites[self.coachman.direction][self.coachman.current_frame],
                (x, y)
            )
        }
        
        for r, row in enumerate(self.grid):
            for c, val in enumerate(row):
                if val in draw_map:
                    draw_map[val](c * GRID_SIZE, r * GRID_SIZE)

    def update_position(self, old_pos, new_pos, entity_type):
        old_r, old_c = old_pos
        new_r, new_c = new_pos
        
        if self[old_r, old_c] != 1:
            self[old_r, old_c] = 0
            
        self[new_r, new_c] = entity_type

    def is_valid_move(self, row, col):
        return 0 <= row < ROWS and 0 <= col < COLS and self.grid[row][col] != 1
