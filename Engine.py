
from constants import *
from Entity import *
from EntityFactory import *
from Game import *


class Engine:
    def __init__(self):
        # Set up the main display and clock
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Coach-Man")
        self.clock = pygame.time.Clock()
        # Initialize maze and entities
        self.maze = Maze()
        
        self.maze.load_coachman_sprites()
        self.maze.load_ghost_sprites()
        self.entity_factory = Factory(self.maze)
        self.coachman = self.entity_factory.create_coachman()
       # self.ghosts = [self.entity_factory.create_ghost() for _ in range(3)]
        # Create 4 ghosts with distinct spawn positions and types
        self.ghosts = self.entity_factory.create_ghosts(4)
        # Link the coachman to the maze (used for drawing)
        self.maze.coachman = self.coachman
        # Set up initial game state
        self.coachman.lives = 3
        self.frame_counter = 0


    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.coachman.move("UP")
                elif event.key == pygame.K_DOWN:
                    self.coachman.move("DOWN")
                elif event.key == pygame.K_LEFT:
                    self.coachman.move("LEFT")
                elif event.key == pygame.K_RIGHT:
                    self.coachman.move("RIGHT")

    def render(self):
        self.screen.fill(BLACK)
        self.maze.draw(self.screen)
        # Draw each ghost on top of the maze
        for ghost in self.ghosts:
            ghost.draw(self.screen)
        
        # Display score and lives
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.coachman.score}", True, WHITE)
        lives_text = font.render(f"Lives: {self.coachman.lives}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(lives_text, (WIDTH-100, 10))
    
        pygame.display.flip()


    def run_game_loop(self):
        self.running = True
        pygame.mixer.music.load('./asset/audio_extraido.wav')
        pygame.mixer.music.play(-1)

        while self.running:
            self.render()
            self.clock.tick(60)
            self.handle_events()
            self.update()

    def display_message(self, message, color=WHITE):
        font = pygame.font.Font(None, 50)
        text = font.render(message, True, color)
        text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
        self.screen.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.delay(2000)



    def check_collision(self):
        for ghost in self.ghosts:
            if self.coachman.position == ghost.position:
                self.coachman.lives -= 1
                if self.coachman.lives > 0:
                    self.display_message("You lost a life!", RED)
                    self.reset_coachman()
                    self.reset_ghosts()
                else:
                    self.display_message("Game Over!", RED)
                    return "GAME_OVER"

    def reset_coachman(self):
        self.coachman.reset_position()

    def reset_ghosts(self):
        for ghost in self.ghosts:
            ghost.reset_position()


    def update(self):
        # Update ghost movement (no time-based animation call)
        if self.frame_counter % 5 == 0:
            for ghost in self.ghosts:
                ghost.move()
            

        # Check for collisions; if game over, stop updating
        if self.check_collision() == "GAME_OVER":
            return False

        # Use the frame counter to update animations.
        # Assuming 60 FPS, updating every 6 frames is roughly equivalent to 0.1 seconds.
        if self.frame_counter % 6 == 0:
            # Update Coachman's animation frame
            self.coachman.current_frame = (self.coachman.current_frame + 1) % COACHMAN_FRAMES_PER_DIR
            # Update each Ghost's animation frame (assuming 8 frames for ghosts)
            for ghost in self.ghosts:
                ghost.current_frame = (ghost.current_frame + 1) % 8

        self.frame_counter += 1
        return True

