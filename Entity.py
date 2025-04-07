
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
        self.direction = "Up"
        self.current_frame = 0
        self.last_update_time = pygame.time.get_ticks()  # NOVO: armazena o tempo do último update
        self.maze.grid[self.position[0]][self.position[1]] = 4
        self.next_direction = "Up"
            # Variáveis para o powerup
        self.power_mode = False
        self.power_mode_end = 0
            
    def activate_powerup(self):
        self.power_mode = True
        self.power_mode_end = pygame.time.get_ticks() + POWERUP_DURATION

    def set_direction(self, direction):
        #self.next_direction = direction
        self.next_direction = direction.capitalize()



    def update(self):
        # Tenta mover na direção desejada
        
        if self.try_move(self.next_direction):
            self.direction = self.next_direction
        else:
            # Se não conseguir, tenta continuar na direção atual
            self.try_move(self.direction)


                # Verifica se o powerup expirou
        if self.power_mode and pygame.time.get_ticks() > self.power_mode_end:
            self.power_mode = False

            # Atualiza a animação baseado no tempo
        now = pygame.time.get_ticks()
        if now - self.last_update_time >= ANIMATION_FRAME_DURATION * 1000:  # converte segundos para milissegundos
            self.current_frame = (self.current_frame + 1) % COACHMAN_FRAMES_PER_DIR
            self.last_update_time = now

    def try_move(self, direction):
        row, col = self.position
        new_row, new_col = row, col

        if direction == "Up":
            new_row -= 1
        elif direction == "Down":
            new_row += 1
        elif direction == "Left":
            new_col -= 1
        elif direction == "Right":
            new_col += 1

        if self.maze.is_valid_move(new_row, new_col):
            if (new_row, new_col) in self.maze.pellets:
                self.maze.pellets.remove((new_row, new_col))
                self.score += 10
            
                    # Se a nova posição for um powerup:
            if self.maze.grid[new_row][new_col] == POWERUP:
                if (new_row, new_col) in self.maze.powerups:
                    self.maze.powerups.pop((new_row, new_col), None)
                self.activate_powerup()  # Ativa o modo power

            self.maze.update_position((row, col), (new_row, new_col), 4)
            self.position = [new_row, new_col]
            self.direction = direction
            #self.current_frame = (self.current_frame + 1) % COACHMAN_FRAMES_PER_DIR
            return True

        return False
    # def move(self, direction):
    #     row, col = self.position
    #     new_row, new_col = row, col
        
    #     if direction == "UP":
    #         new_row -= 1
    #     elif direction == "DOWN":
    #         new_row += 1
    #     elif direction == "LEFT":
    #         new_col -= 1
    #     elif direction == "RIGHT":
    #         new_col += 1
        
    #     if self.maze.is_valid_move(new_row, new_col):
    #         if (new_row, new_col) in self.maze.pellets:
    #             self.maze.pellets.remove((new_row, new_col))
    #             self.score += 10
            
    #         self.maze.update_position((row, col), (new_row, new_col), 4)
    #         self.position = [new_row, new_col]
           
    #         self.direction = "Right" if direction.upper() == "RIGHT" else direction.capitalize()
    #         # Advance animation frame
    #         self.current_frame = (self.current_frame + 1) % COACHMAN_FRAMES_PER_DIR
            
    # def reset_position(self):
    #     self.position = self.maze.find_initial_pos(4)
    #     self.maze.grid[self.position[0]][self.position[1]] = 4
    def reset_position(self):
        self.position = self.maze.find_initial_pos(4)
        self.direction = "Up"
        self.next_direction = "Up"
        self.current_frame = 0
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
        self.last_update_time = pygame.time.get_ticks()  # NOVO
    
    def update_animation(self):
        now = pygame.time.get_ticks()
        if now - self.last_update_time >= ANIMATION_FRAME_DURATION * 1000:
            self.current_frame = (self.current_frame + 1) % 8  # 8 frames para os fantasmas
            self.last_update_time = now

    def move(self):
        # Convert positions to tuples to ensure consistency.
        start = tuple(self.position)
        target = tuple(self.maze.coachman.position)  # Assume coachman is linked to the maze
        

          # Se o Coach-Man está em power mode, os fantasmas fogem
        if self.maze.coachman.power_mode:
            best_move = None
            max_distance = -1
            for dr, dc in self.directions:
                new_row, new_col = self.position[0] + dr, self.position[1] + dc
                if self.maze.is_valid_move(new_row, new_col):
                    # Calcula a distância de Manhattan para o Coach-Man
                    distance = abs(new_row - target[0]) + abs(new_col - target[1])
                    if distance > max_distance:
                        max_distance = distance
                        best_move = (new_row, new_col)
            if best_move:
                self.maze.update_position(start, best_move, 3)
                self.position = list(best_move)
                return
            # Se nenhuma direção melhora a distância, pode optar por um movimento aleatório
            random.shuffle(self.directions)
            for dr, dc in self.directions:
                new_row, new_col = self.position[0] + dr, self.position[1] + dc
                if self.maze.is_valid_move(new_row, new_col):
                    self.maze.update_position(start, (new_row, new_col), 3)
                    self.position = [new_row, new_col]
                    return
        else:
            # Comportamento normal: usa A* para perseguir o Coach-Man
            path = self.astar(start, target, self.maze.grid)
            if path and len(path) > 1:
                next_step = path[1]
                self.maze.update_position(start, next_step, 3)
                self.position = list(next_step)
            else:
                # Fallback: movimento aleatório se não encontrar um caminho
                random.shuffle(self.directions)
                for dr, dc in self.directions:
                    new_row, new_col = self.position[0] + dr, self.position[1] + dc
                    if self.maze.is_valid_move(new_row, new_col):
                        self.maze.update_position(start, (new_row, new_col), 3)
                        self.position = [new_row, new_col]
                        break
        # # Try to compute a path using A*
        # path = self.astar(start, target, self.maze.grid)
        
        # if path and len(path) > 1:
        #     # The next step in the path (path[0] is the current position)
        #     next_step = path[1]
        #     self.maze.update_position(start, next_step, 3)
        #     self.position = list(next_step)
        # else:
        #     # Fallback: if no path is found, move randomly.
        #     row, col = self.position
        #     random.shuffle(self.directions)
        #     for dr, dc in self.directions:
        #         new_row, new_col = row + dr, col + dc
        #         if self.maze.is_valid_move(new_row, new_col):
        #             self.maze.update_position((row, col), (new_row, new_col), 3)
        #             self.position = [new_row, new_col]
        #             break

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

    # def draw(self, screen):
    #     # Get the correct sprite frames for this ghost type from the maze
    #     ghost_frames = self.maze.ghost_sprites[self.type]
    #     # Draw the current frame at the ghost's position
    #     x = self.position[1] * GRID_SIZE
    #     y = self.position[0] * GRID_SIZE
    #     screen.blit(ghost_frames[self.current_frame], (x, y))
    def draw(self, screen):
        ghost_frames = self.maze.ghost_sprites[self.type]
        sprite = ghost_frames[self.current_frame]
        x = self.position[1] * GRID_SIZE
        y = self.position[0] * GRID_SIZE
        # Center the ghost sprite in the cell
        sprite_rect = sprite.get_rect(center=(x + GRID_SIZE // 2, y + GRID_SIZE // 2))

        # Se o power mode estiver ativo, desenha com um contorno azul (ou modifique a cor)
        if self.maze.coachman.power_mode:
            # Cria uma cópia do sprite para alterar a cor (exemplo simples)
            tinted_sprite = sprite.copy()
            tinted_sprite.fill((BLUE), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(tinted_sprite, sprite_rect)
        else:
            screen.blit(sprite, sprite_rect)

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
        self.ghost_sprites = {}  # Já é um dicionário para os fantasmas

        # Define as posições dos powerups e associa cada posição a um índice (0 a 3)
        self.powerups = {
            (1, 2): 0,
            (1, COLS - 2): 1,
            (ROWS - 2, 2): 2,
            (ROWS - 2, COLS - 2): 3
        }
        for pos in self.powerups:
            r, c = pos
            self.grid[r][c] = POWERUP

        # Carrega as imagens do powerup
        self.load_powerup_images()

    def reset(self):
        """Reset maze to initial state while preserving sprites and coachman reference"""
        self.pellets = {
            (r, c) for r, row in enumerate(INITIAL_GRID)
            for c, val in enumerate(row) if val == 2
        }
        self.grid = [row[:] for row in INITIAL_GRID]
        
    def load_powerup_images(self):
     
        self.powerup_images = []
        for i in range(1, 5):
            filename = f"./asset/powerup{i}.png"
            try:
                img = pygame.image.load(filename).convert_alpha()
            
                # Redimensiona a imagem para caber na célula do grid, se necessário:
                img = pygame.transform.scale(img, (GRID_SIZE, GRID_SIZE))
                self.powerup_images.append(img)
            except Exception as e:
                print(f"Erro ao carregar {filename}: {e}")
        print("Powerup images carregadas:", len(self.powerup_images))

    def load_ghost_sprites(self):
        # Load ghost sprites for each ghost type and store them in a dictionary.
        ghost_types = ["BLINKY", "PINKY", "INKY", "CLYDE"]
        self.ghost_sprites = {}
        scale_factor = 1.5  # Increase ghost size similarly
        new_size = (int(GRID_SIZE * scale_factor), int(GRID_SIZE * scale_factor))
       
        for ghost in ghost_types:
            frames = []
            for i in range(1, 9):
                filename = f"./asset/{ghost}{i:02d}.png"
                img = pygame.image.load(filename)
                # Scale the image to GRID_SIZE
                img = pygame.transform.scale(img, new_size)
                 # Use smoothscale para suavizar o redimensionamento
                img = pygame.transform.smoothscale(img, new_size)
                frames.append(img)
            self.ghost_sprites[ghost] = frames

        
    def load_coachman_sprites(self):    
        # We assume the assets already exist in the "asset" folder.
        # Keys: "Down", "Right", "Left", "Up". Using "Righ" for the right direction.
        directions = ["Down", "Right", "Left", "Up"]
        self.coachman_sprites = {}
        # Set a scaling factor (e.g., 1.5 times larger than a cell)
        scale_factor = 1.5
        new_size = (int(GRID_SIZE * scale_factor), int(GRID_SIZE * scale_factor))

        for d in directions:
            frames = []
            for i in range(1, 4):  # 3 frames per direction
                filename = f"./asset/coachMan{d}0{i}.png"
                img = pygame.image.load(filename)
                img = pygame.transform.scale(img, new_size)
                 # Use smoothscale para suavizar o redimensionamento
                img = pygame.transform.smoothscale(img, new_size)
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
        # Set wall scale relative to GRID_SIZE (e.g., 60% of the cell)
        wall_scale = 0.6
        wall_size = int(GRID_SIZE * wall_scale)
        offset = (GRID_SIZE - wall_size) // 2

        # Define a dictionary that maps cell values to drawing functions.
        draw_map = {
            # For walls (value 1), draw a centered smaller rectangle.
            1: lambda x, y: pygame.draw.rect(screen, BLUE, (x + offset, y + offset, wall_size, wall_size)),
            # For pellets (value 2), draw a circle.
            2: lambda x, y: pygame.draw.circle(screen, WHITE, (x + GRID_SIZE // 2, y + GRID_SIZE // 2), 5),
            # For coachman (value 4), blit the current sprite.
            4: lambda x, y: screen.blit(
                self.coachman_sprites[self.coachman.direction][self.coachman.current_frame],
                (x, y)
            ),
           # POWERUP: lambda x, y: pygame.draw.circle(screen, (0, 255, 0), (x + GRID_SIZE // 2, y + GRID_SIZE // 2), 8)
    }
        
        
        # Loop over the grid, computing x and y positions for each cell,
        # then call the corresponding drawing function.
        for r, row in enumerate(self.grid):
            for c, val in enumerate(row):
                if val in draw_map:
                    x = c * GRID_SIZE
                    y = r * GRID_SIZE
                    draw_map[val](x, y)
                elif val == POWERUP:
                    # Obtenha o índice da imagem a partir do dicionário de powerups
                    powerup_index = self.powerups.get((r, c), 0)
                    # Desenha a imagem do powerup na posição (x, y)
                    if self.powerup_images:
                        screen.blit(self.powerup_images[powerup_index], (x, y))
                    else:
                        # Caso as imagens não tenham sido carregadas, desenha um placeholder
                        pygame.draw.rect(screen, (0, 255, 0), (x, y, GRID_SIZE, GRID_SIZE))

    # def draw(self, screen):


    #     wall_size = int(GRID_SIZE * 0.6)  # e.g., 60% of the cell size
    #     offset = (GRID_SIZE - wall_size) // 2
    #     pygame.draw.rect(screen, BLUE, (x + offset, y + offset, wall_size, wall_size))

    #     draw_map = {
    #         1: lambda x, y: pygame.draw.rect(screen, BLUE, (x + offset, y + offset, wall_size, wall_size)),
            
    #         # 1: lambda x, y: pygame.draw.rect(screen, BLUE, (x, y, GRID_SIZE, GRID_SIZE)),
    #         2: lambda x, y: pygame.draw.circle(screen, WHITE, (x + GRID_SIZE // 2, y + GRID_SIZE // 2), 5),
    #         4: lambda x, y: self._draw_coachman(screen, x, y)
            
    #     }
    
    #     for r, row in enumerate(self.grid):
    #         for c, val in enumerate(row):
    #             if val in draw_map:
    #                 draw_map[val](c * GRID_SIZE, r * GRID_SIZE)

    def _draw_coachman(self, screen, x, y):
        # Get current sprite for coachman
        sprite = self.coachman_sprites[self.coachman.direction][self.coachman.current_frame]
        # Center the sprite in the cell
        sprite_rect = sprite.get_rect(center=(x + GRID_SIZE // 2, y + GRID_SIZE // 2))
        screen.blit(sprite, sprite_rect)
    
    def update_position(self, old_pos, new_pos, entity_type):
        old_r, old_c = old_pos
        new_r, new_c = new_pos

        # Limpa a posição antiga
        if entity_type == 3:  # Ghost
            # Se a posição anterior tinha um pellet, restaura ele
            if (old_r, old_c) in self.pellets:
                self.grid[old_r][old_c] = 2
            else:
                self.grid[old_r][old_c] = 0
        else:
            # Coachman ou outro tipo — sempre limpa
            self.grid[old_r][old_c] = 0

        # Atualiza nova posição
        if entity_type == 3 and self.grid[new_r][new_c] == 2:
            pass  # Fantasma não sobrescreve visualmente o pellet
        else:
            self.grid[new_r][new_c] = entity_type
    # def update_position(self, old_pos, new_pos, entity_type):
    #     old_r, old_c = old_pos
    #     new_r, new_c = new_pos
        
    #     if self[old_r, old_c] == 3:
    #         # Se o fantasma saiu de um lugar com pellet, restaure o pellet
    #         if (old_r, old_c) in self.pellets:
    #             self[old_r, old_c] = 2
    #         else:
    #             self[old_r, old_c] = 0

    #     # Não sobrescreve o pellet com o valor do fantasma no grid
    #     if entity_type == 3 and self.grid[new_r][new_c] == 2:
    #         pass  # mantém o pellet visível
    #     else:
    #         self[new_r, new_c] = entity_type
            
    #     self[new_r, new_c] = entity_type

    def is_valid_move(self, row, col):
        return 0 <= row < ROWS and 0 <= col < COLS and self.grid[row][col] != 1
