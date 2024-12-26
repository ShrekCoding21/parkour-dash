import pygame

class Artifact(pygame.sprite.Sprite):
    def __init__(self, image, position, name):
        """
        Initialize an Artifact object.

        Args:
            image (pygame.Surface): The image representing the artifact.
            position (tuple): The (x, y) position of the artifact.
            name (str): The name or ID of the artifact.
        """
        super().__init__()
        self.image = pygame.transform.scale(image, (50, 50))  # Scale the image to a standard size
        self.rect = self.image.get_rect(topleft=position)
        self.name = name
        self.collected = False

    def collect(self):
        """
        Mark the artifact as collected.
        """
        self.collected = True

    def reset(self):
        """
        Reset the artifact to its uncollected state.
        """
        self.collected = False
