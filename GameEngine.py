
import pygame
import random
from constants import *
from Entity import Pacman, Ghost, Maze
from EntityFactory import Factory
from Menu import Menu



class Game:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pac-Man Refactored")
        self.clock = pygame.time.Clock()
        self.maze = Maze()
        self.entity_factory = Factory(self.maze)
        self.pacman = self.entity_factory.create_pacman()
        self.ghosts = [self.entity_factory.create_ghost() for _ in range(3)]

    def check_collision(self):
        for ghost in self.ghosts:
            if self.pacman.position == ghost.position:
                self.pacman.lives -= 1
                
                if self.pacman.lives > 0:
                    self.display_message("You lost a life!", RED)
                else:
                    self.display_message("Game Over!", RED)
                    pygame.quit()
                    exit()
                
                self.reset_pacman()

    def reset_pacman(self):
        self.pacman.reset_position()

    def display_message(self, message, color=WHITE):
        font = pygame.font.Font(None, 50)
        text = font.render(message, True, color)
        text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
        self.screen.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.delay(2000)

    def run(self):
        running = True
        while running:
            menu = Menu(self.window)
            menu.run()
            self.screen.fill(BLACK)
            self.maze.draw(self.screen)
            
            # Display score and lives
            font = pygame.font.Font(None, 36)
            score_text = font.render(f"Score: {self.pacman.score}", True, WHITE)
            lives_text = font.render(f"Lives: {self.pacman.lives}", True, WHITE)
            self.screen.blit(score_text, (10, 10))
            self.screen.blit(lives_text, (WIDTH-100, 10))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.pacman.move("UP")
                    elif event.key == pygame.K_DOWN:
                        self.pacman.move("DOWN")
                    elif event.key == pygame.K_LEFT:
                        self.pacman.move("LEFT")
                    elif event.key == pygame.K_RIGHT:
                        self.pacman.move("RIGHT")
            
            for ghost in self.ghosts:
                ghost.move()
            
            self.check_collision()
            pygame.display.flip()
            self.clock.tick(5)
        
        pygame.quit()
