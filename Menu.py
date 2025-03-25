import pygame


class Menu:

    def __init__(self, window):
        self.window = window
        self.surf - pygame.image.load('./asset/marcalHead.jpg')
        self.rect = self.surf.get_rect(left=0, top=0)


    def run(self, ):
        self.window.blit(source=self.surf, dest=self.rect)
        pygame.display.flip()