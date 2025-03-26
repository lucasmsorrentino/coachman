
import pygame
import random
from constants import *
from Entity import Coachman, Ghost, Maze
from EntityFactory import Factory
from Menu import Menu



class Game:

    def __init__(self):
        
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Coach-Man")
        self.clock = pygame.time.Clock()
        self.maze = Maze()
        self.entity_factory = Factory(self.maze)
        self.coachman = self.entity_factory.create_coachman()
        self.ghosts = [self.entity_factory.create_ghost() for _ in range(3)]
        self.animation_frame = 0
        self.animation_speed = 10
        self.maze.load_coachman_sprites()
        self.maze.coachman = self.coachman

    def check_collision(self):
        for ghost in self.ghosts:
            if self.coachman.position == ghost.position:
                self.coachman.lives -= 1
                
                if self.coachman.lives > 0:
                    self.display_message("You lost a life!", RED)
                else:
                    self.display_message("Game Over!", RED)
                    pygame.quit()
                    exit()
                
                self.reset_coachman()

    def reset_coachman(self):
        self.coachman.reset_position()

    def display_message(self, message, color=WHITE):
        font = pygame.font.Font(None, 50)
        text = font.render(message, True, color)
        text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
        self.screen.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.delay(2000)

    def run(self):
        pygame.mixer.init()
        running = True
        while running:
            menu = Menu(self.screen)
            menu_return = menu.run()

            if menu_return == MENU_OPTION[1]:
                pass
            elif menu_return == MENU_OPTION[2]:
                pygame.quit()
                quit()

            elif menu_return == MENU_OPTION[0]:
                # Start the game
                pygame.mixer.music.load('./asset/audio_extraido.wav')
                pygame.mixer.music.play(-1)
                self.coachman.score = 0
                self.coachman.lives = 3
                self.reset_coachman()
                self.maze.reset()
                self.ghosts = [self.entity_factory.create_ghost() for _ in range(3)]

                self.clock.tick(60)



                self.screen.fill(BLACK)
                self.maze.draw(self.screen)
            
                # Display score and lives
                font = pygame.font.Font(None, 36)
                score_text = font.render(f"Score: {self.coachman.score}", True, WHITE)
                lives_text = font.render(f"Lives: {self.coachman.lives}", True, WHITE)
                self.screen.blit(score_text, (10, 10))
                self.screen.blit(lives_text, (WIDTH-100, 10))
            
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_UP:
                            self.coachman.move("UP")
                        elif event.key == pygame.K_DOWN:
                            self.coachman.move("DOWN")
                        elif event.key == pygame.K_LEFT:
                            self.coachman.move("LEFT")
                        elif event.key == pygame.K_RIGHT:
                            self.coachman.move("RIGHT")
            
                for ghost in self.ghosts:
                    ghost.move()
            
                self.check_collision()
                pygame.display.flip()
                # Update animation frames
                current_time = pygame.time.get_ticks()
                delta_time = (current_time - self.coachman.frame_timer) / 1000.0
                
                if delta_time >= ANIMATION_FRAME_DURATION:
                    self.coachman.current_frame = (self.coachman.current_frame + 1) % COACHMAN_FRAMES_PER_DIR
                    self.coachman.frame_timer = current_time
                
                self.clock.tick(60)
        
            pygame.quit()
