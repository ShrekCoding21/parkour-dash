import pygame
import sys

pygame.init()
window_size = (800, 600)
screen = pygame.display.set_mode(window_size)

player = pygame.Rect((300, 250, 50, 50))
pygame.display.set_caption("Karthikeya Abhimanyu Ainapurapu")

import pygame


class Player_1(pygame.sprite.Sprite):
    
    def __init__(self, name, sprite_sheet, tree_type, x, y):
        super().__init__()
        self.name = name
        
    def get_image(self, frame_index):
        """Extracts the correct frame from the sprite sheet."""
        # Calculate the x position of the current frame based on the type and frame index
        x = self.start_x + (frame_index * self.frame_width)
        y = 0  # Assuming the tree sprites are in the first row of the sprite sheet
        # Extract the frame from the sprite sheet
        image = self.sprite_sheet.subsurface(pygame.Rect(x, y, self.frame_width, self.frame_height))
        return image

    def update(self):
        """Update the sprite's animation."""
        self.frame_index += self.animation_speed
        if self.frame_index >= 3:  # Assuming 3 frames of animation
            self.frame_index = 0
        # Update the image to the new frame
        self.image = self.get_image(int(self.frame_index))

# hello world heheheha

run = True
while run:

    screen.fill((65, 166, 15))
    pygame.draw.rect(screen, (255, 0, 0), player)

    key = pygame.key.get_pressed()
    if key[pygame.K_a]:
        player.move_ip(-1, 0)
    elif key[pygame.K_d]:
        player.move_ip(1, 0)
    elif key[pygame.K_w]:
        player.move_ip(0, -1)
    elif key[pygame.K_s]:
        player.move_ip(0, 1)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()
