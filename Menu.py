import pygame
from constants import *


class Menu:

    def __init__(self, screen):
        self.screen = screen
        self.surf = pygame.image.load('./asset/marcalHead.png')
        self.rect = self.surf.get_rect(left=0, top=HEIGHT/5.5)


    def run(self, ):
        menu_option = 0
        pygame.mixer.init()
        pygame.mixer.music.load('./asset/videoplayback_audio.wav')
        pygame.mixer.music.play(-1)
        while True:
            self.screen.blit(source=self.surf, dest=self.rect)
            self.menu_text(90, (YELLOW), (WIDTH/2, HEIGHT/10), "Coach-Man")

            for i in range(len(MENU_OPTION)):
                if i == menu_option:
                    self.menu_text(50, (YELLOW), (WIDTH/9, HEIGHT/2.8 + 60 * i), MENU_OPTION[i])
                else:
                    self.menu_text(50, (WHITE), (WIDTH/9, HEIGHT/2.8 + 60 * i), MENU_OPTION[i])

           
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
                    elif event.key == pygame.K_RETURN:
                        if menu_option == 0:
                            return MENU_OPTION[menu_option]
                      
              

    def menu_text(self, text_size: int, text_color: tuple, text_position: tuple, text: str):
        font = pygame.font.SysFont("helvetica", text_size)
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=text_position)
        self.screen.blit(text_surface, text_rect)
