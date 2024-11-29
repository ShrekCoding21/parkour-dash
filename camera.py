import pygame
from Players.player import Player
from Platforms.platform import Platform

class Camera():
    
    def __init__(self, width, height, window_size):
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.window_size = window_size

    def apply(self, obj):

        if isinstance(obj, Player):
            return obj.rect.move(-self.camera_rect.topleft[0], -self.camera_rect.topleft[1])
        elif isinstance(obj, Platform):
            return pygame.Rect(
                obj.position.x - self.camera_rect.topleft[0],
                obj.position.y - self.camera_rect.topleft[1],
                obj.dimensions[0],
                obj.dimensions[1]
            )
        return obj
    
    def update(self, player):

        x = player.position.x - 500
        y = player.position.y - (self.window_size[1] // 2)

        x = max(0, min(x, self.width - self.window_size[0]))
        y = max(0, min(y, self.height - self.window_size[0]))

        self.camera_rect = pygame.Rect(x, y, self.width, self.height)