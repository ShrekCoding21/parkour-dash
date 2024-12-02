import pygame
from Players.player import Player
from Platforms.platform import Platform

class Camera():
    
    def __init__(self, width, height, window_size):
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.window_size = window_size
        self.zoom = 0.3
        self.margin = 100
        self.is_active = True

    def apply(self, obj):

        if self.is_active:

            if isinstance(obj, Player):
                rect = obj.rect.copy()
                rect.x = (rect.x - self.camera_rect.x) * self.zoom
                rect.y = (rect.y - self.camera_rect.y) * self.zoom
                rect.width *= self.zoom
                rect.height *= self.zoom
                return rect
            
            elif isinstance(obj, Platform):
                scaled_rect = pygame.Rect(
                    (obj.position.x - self.camera_rect.x) * self.zoom,
                    (obj.position.y - self.camera_rect.y) * self.zoom,
                    obj.dimensions[0] * self.zoom,
                    obj.dimensions[1] * self.zoom
                )
                return scaled_rect
        
        else:

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

    
    def update(self, players, player):
        
        if self.is_active:

            min_x = min(player.position.x for player in players)
            max_x = max(player.position.x for player in players)
            min_y = min(player.position.y for player in players)
            max_y = max(player.position.y for player in players)

            min_x -= self.margin
            max_x += self.margin
            min_y -= self.margin
            max_y += self.margin

            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2

            bounding_width = max_x - min_x
            bounding_height = max_y - min_y
            zoom_x = self.window_size[0] / bounding_width
            zoom_y = self.window_size[1] / bounding_height

            self.zoom = min(zoom_x, zoom_y, 1.0)

            camera_width = self.window_size[0] / self.zoom
            camera_height = self.window_size[1] / self.zoom
            self.camera_rect = pygame.Rect(
                max(0, min(center_x - camera_width / 2, self.width - camera_width)),
                max(0, min(center_y - camera_height / 2, self.height - camera_height)),
                camera_width,
                camera_height
            )
        
        if not self.is_active:
            
            x = player.position.x - 500
            y = player.position.y - (self.window_size[1] // 2)

            x = max(0, min(x, self.width - self.window_size[0]))
            y = max(0, min(y, self.height - self.window_size[0]))

            self.camera_rect = pygame.Rect(x, y, self.width, self.height)
