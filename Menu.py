
import pygame
from score_db import get_high_scores
from constants import *


class Menu:

    def __init__(self, screen):
        self.screen = screen
        
        self.surf = pygame.image.load('./asset/marcalHead.png')
        
        coach_size = self.surf.get_size()

        # Set the display mode to match the asset background size
        screen = pygame.display.set_mode(coach_size)

        self.rect = self.surf.get_rect(left=0, top=0)


    def run(self, ):
        menu_option = 0
        pygame.mixer.init()
        pygame.mixer.music.load('./asset/videoplayback_audio.wav')
        pygame.mixer.music.play(-1)
        while True:
                # Clear the screen before drawing the menu
            self.screen.fill(BLACK)
                # Draw the header image and menu title
            self.screen.blit(source=self.surf, dest=self.rect)
            self.menu_text(65, (YELLOW), (WIDTH/2, HEIGHT/8), "Coach-Man")


                # Draw each menu option
            for i in range(len(MENU_OPTION)):
                if i == menu_option:
                    self.menu_text(35, (RED), (WIDTH/2, HEIGHT/2 + 120 * i), MENU_OPTION[i])
                else:
                    self.menu_text(30, (YELLOW), (WIDTH/2, HEIGHT/2 + 120 * i), MENU_OPTION[i])

           
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_DOWN:
                        if menu_option < len(MENU_OPTION) - 1:
                            menu_option += 1
                        else:
                            menu_option = 0
                    elif event.key == pygame.K_UP:
                        if menu_option > 0:
                            menu_option -= 1
                        else:
                            menu_option = len(MENU_OPTION) - 1
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        return MENU_OPTION[menu_option]
                                

    def menu_text(self, text_size: int, text_color: tuple, text_position: tuple, text: str):
        font = pygame.font.Font('./asset/PressStart2P-Regular.ttf', text_size)
        lines = text.split("\n")
        # Calculate total height of the text block
        total_height = len(lines) * font.get_linesize()
        # Compute starting y position so that the text block is centered vertically around text_position[1]
        start_y = text_position[1] - total_height // 2

        for i, line in enumerate(lines):
            text_surface = font.render(line, True, text_color)
            # Center each line horizontally at text_position[0] and adjust the y position for each line
            text_rect = text_surface.get_rect(center=(text_position[0], start_y + i * font.get_linesize()))
            self.screen.blit(text_surface, text_rect)


