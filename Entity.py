
from dataclasses import dataclass
from typing import List, Set, Tuple
import pygame
import random
from constants import *
import heapq





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
        self.direction = "Right"
        self.current_frame = 0
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
           
            self.direction = "Right" if direction.upper() == "RIGHT" else direction.capitalize()
            # Advance animation frame
            self.current_frame = (self.current_frame + 1) % COACHMAN_FRAMES_PER_DIR
            
    def reset_position(self):
        self.position = self.maze.find_initial_pos(4)
        self.maze.grid[self.position[0]][self.position[1]] = 4

class Ghost:
    def __init__(self, maze, position):
        self.maze = maze
        self.position = list(position)  # Ensure it's mutable
        self.initial_position = list(position)  # Store this unique spawn position
        # Optionally assign type here or via factory:
        self.type = random.choice(["BLINKY", "PINKY", "INKY", "CLYDE"])
        self.directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        self.maze.grid[self.position[0]][self.position[1]] = 3
        # Animation attributes for ghost (8 frames)
        self.current_frame = 0

    def move(self):
        # Convert positions to tuples to ensure consistency.
        start = tuple(self.position)
        target = tuple(self.maze.coachman.position)  # Assume coachman is linked to the maze

        # Try to compute a path using A*
        path = self.astar(start, target, self.maze.grid)
        
        if path and len(path) > 1:
            # The next step in the path (path[0] is the current position)
            next_step = path[1]
            self.maze.update_position(start, next_step, 3)
            self.position = list(next_step)
        else:
            # Fallback: if no path is found, move randomly.
            row, col = self.position
            random.shuffle(self.directions)
            for dr, dc in self.directions:
                new_row, new_col = row + dr, col + dc
                if self.maze.is_valid_move(new_row, new_col):
                    self.maze.update_position((row, col), (new_row, new_col), 3)
                    self.position = [new_row, new_col]
                    break

    def astar(self, start, goal, grid):
        
        # Define the Manhattan distance heuristic.
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])
            
        # The four possible movement directions (up, down, left, right)
        neighbors = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}

        while open_set:
            current_f, current = heapq.heappop(open_set)
            if current == goal:
                # Reconstruct the path from start to goal.
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            for dx, dy in neighbors:
                neighbor = (current[0] + dx, current[1] + dy)
                # Check if neighbor is within grid bounds (using ROWS and COLS from constants)
                if not (0 <= neighbor[0] < ROWS and 0 <= neighbor[1] < COLS):
                    continue
                # Only consider cells that are not walls (wall cells are represented by 1)
                if grid[neighbor[0]][neighbor[1]] == 1:
                    continue
                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    f = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f, neighbor))
                    came_from[neighbor] = current

        # Return None if no path is found.
        return None

    def reset_position(self):
        self.position = list(self.initial_position)
        self.maze.grid[self.position[0]][self.position[1]] = 3

    '''def update_animation(self):
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - self.frame_timer) / 1000.0
        if delta_time >= ANIMATION_FRAME_DURATION:
            # Advance frame modulo 8 frames
            self.current_frame = (self.current_frame + 1) % 8
            self.frame_timer = current_time'''

    def draw(self, screen):
        # Get the correct sprite frames for this ghost type from the maze
        ghost_frames = self.maze.ghost_sprites[self.type]
        # Draw the current frame at the ghost's position
        x = self.position[1] * GRID_SIZE
        y = self.position[0] * GRID_SIZE
        screen.blit(ghost_frames[self.current_frame], (x, y))


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
        self.ghost_sprites = []  # New attribute for ghost assets

    def reset(self):
        """Reset maze to initial state while preserving sprites and coachman reference"""
        self.pellets = {
            (r, c) for r, row in enumerate(INITIAL_GRID)
            for c, val in enumerate(row) if val == 2
        }
        self.grid = [row[:] for row in INITIAL_GRID]
        


    def load_ghost_sprites(self):
        # Load ghost sprites for each ghost type and store them in a dictionary.
        ghost_types = ["BLINKY", "PINKY", "INKY", "CLYDE"]
        self.ghost_sprites = {}
       
        for ghost in ghost_types:
            frames = []
            for i in range(1, 9):
                filename = f"./asset/{ghost}{i:02d}.png"
                img = pygame.image.load(filename)
                # Scale the image to GRID_SIZE
                
                frames.append(img)
            self.ghost_sprites[ghost] = frames

        
    def load_coachman_sprites(self):    
        # We assume the assets already exist in the "asset" folder.
        # Keys: "Down", "Right", "Left", "Up". Using "Righ" for the right direction.
        directions = ["Down", "Right", "Left", "Up"]
        self.coachman_sprites = {}
        
        for d in directions:
            frames = []
            for i in range(1, 4):  # 3 frames per direction
                filename = f"./asset/coachMan{d}0{i}.png"
                img = pygame.image.load(filename)
                
                frames.append(img)
            self.coachman_sprites[d] = frames
     



       
    

    def __getitem__(self, idx):
        return self.grid[idx[0]][idx[1]]
        
    def __setitem__(self, idx, value):
        r, c = idx
        if self.grid[r][c] == 2:
            self.pellets.discard((r, c))
        if value == 2:
            self.pellets.add((r, c))
        self.grid[r][c] = value

    #def find_initial_pos(self, entity_type):
     #   return next(
      #      ((r, c) for r, row in enumerate(self.grid)
       #      for c, val in enumerate(row) if val == entity_type),
        #    (1, 1)  # default
        #)
    def find_all_initial_pos(self, entity_type):
        return [
            (r, c) for r, row in enumerate(self.grid)
            for c, val in enumerate(row) if val == entity_type
        ]
    def find_initial_pos(self, entity_type):
        positions = [
            (r, c) for r, row in enumerate(self.grid)
            for c, val in enumerate(row) if val == entity_type
        ]
        if positions:
            return random.choice(positions)
        else:
            return (1, 1)  # default if none found

    def draw(self, screen):
        draw_map = {
            1: lambda x, y: pygame.draw.rect(screen, BLUE, (x, y, GRID_SIZE, GRID_SIZE)),
            2: lambda x, y: pygame.draw.circle(screen, WHITE, (x + GRID_SIZE // 2, y + GRID_SIZE // 2), 5),
            4: lambda x, y: screen.blit(
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
