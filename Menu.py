import pygame
from constants import *


class Menu:

    def __init__(self, screen):
        self.screen = screen
        self.surf = pygame.image.load('./asset/marcalHead.png')
        self.rect = self.surf.get_rect(left=0, top=HEIGHT/2)


    def run(self, ):
        pygame.mixer_music.load('./asset/audio_extraido.mp3')
        pygame.mixer_music.play(-1)
        while True:
            self.menu_text(70, (YELLOW), (WIDTH/2, HEIGHT/8), "Coach-Man")

           # for i in range(len(MENU_OPTION)):
            #    self.menu_text(50, (WHITE), (WIDTH/8, HEIGHT/6 + 30 * i), MENU_OPTION[i])

            self.menu_text(50, (WHITE), (WIDTH/8, HEIGHT/6), "Play")
            self.menu_text(50, (WHITE), (WIDTH/8, HEIGHT/4), "Score")
            self.menu_text(50, (WHITE), (WIDTH/8, HEIGHT/3), "Exit")
            self.screen.blit(source=self.surf, dest=self.rect)
            pygame.display.flip()

            for event in pygame,event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

    def menu_text(self, text_size: int, text_color: tuple, text_position: tuple, text: str):
        font = pygame.font.Font("helvetica", text_size)
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=text_position)
        self.screen.blit(text_surface, text_rect)