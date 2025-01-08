import pygame

class Ladder:
    def __init__(self, x, y, height):
        """
        Initializes a Ladder object.

        Parameters:
        x (int): The x-coordinate of the ladder's position.
        y (int): The y-coordinate of the ladder's position.
        height (int): The height of the ladder.
        image_path (str): Path to the ladder's image file.
        """
        self.x = x
        self.y = y
        self.height = height
        self.width = 10  # Default width of the ladder
        self.image = pygame.image.load("Levels/Magnus25/assets/ladder.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.on_ladder = False

    def draw(self, camera, surface):
        """
        Draws the ladder on the given surface, taking the camera position into account.

        Parameters:
        surface (pygame.Surface): The surface to draw the ladder on.
        camera: The camera object that provides the apply method to adjust for the camera's position.
        """
        ladder_rect = camera.apply(self)
        surface.blit(self.image, (ladder_rect.x, ladder_rect.y))
