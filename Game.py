import pygame
import Engine
from constants import *
from Menu import Menu
from Engine import Engine
from score_db import get_high_scores
from score_db import insert_score


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
                self.display_scores()
            elif menu_return == MENU_OPTION[2]:  # Exit
                pygame.quit()
                return
            elif menu_return == MENU_OPTION[0]:  # Play
                engine = Engine()
                final_score = engine.run_game_loop()
                scores = get_high_scores()
                if len(scores) < 10 or final_score > scores[-1]:  # Compare against lowest high score
                    initials = self.get_player_initials(final_score)
                    if initials:  # Only save if player entered initials
                        insert_score(initials, final_score)
                self.display_scores()
              

    def get_player_initials(self, score):
        """Capture 3-letter player input using pygame"""
        font = pygame.font.Font(None, 48)
        input_box = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 25, 200, 50)
        color_inactive = pygame.Color('lightskyblue3')
        color_active = pygame.Color('dodgerblue2')
        color = color_inactive
        active = True
        text = ''
    
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return ''
                if event.type == pygame.KEYDOWN:
                    if active:
                        if event.key == pygame.K_RETURN:
                            return text[:3].upper()
                        elif event.key == pygame.K_BACKSPACE:
                            text = text[:-1]
                        else:
                            text += event.unicode
                            text = text[:3].upper()

            self.screen.fill((30, 30, 30))
            txt_surface = font.render(text, True, color)
            width = max(200, txt_surface.get_width()+10)
            input_box.w = width
            self.screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
            pygame.draw.rect(self.screen, color, input_box, 2)

            score_text = font.render(f"Final Score: {score}", True, (255, 255, 255))
            self.screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//3))

            prompt = font.render("Enter 3 initials:", True, (255, 255, 255))
            self.screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 - 100))

            pygame.display.flip()
            pygame.time.wait(10)

    def display_scores(self):
        high_scores = get_high_scores()
        pygame.mixer.music.load('./asset/audio_cortado.wav')
        pygame.mixer.music.play(-1)

        self.screen.fill(BLACK)
    
        font = pygame.font.Font('./asset/PressStart2P-Regular.ttf', 33)
        
        title = font.render("High Scores", True, (255, 255, 0))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        y = 120
        for initials, score, date in high_scores:
            score_text = font.render(f"{initials} - {score} - {date.split()[0]}", True, (255, 255, 255))
            self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, y))
            y += 40

        font = pygame.font.Font('./asset/PressStart2P-Regular.ttf', 20)
        prompt = font.render("Press any key to return to the menu", True, (255, 255, 255))
        self.screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT - 100))
        
        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN or event.type == pygame.QUIT:
                    waiting = False
