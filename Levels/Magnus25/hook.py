import pygame
import math

class Hook:
    def __init__(self, x, y, length, swing_angle, speed, image=None):
        """
        Initializes the Hook object.

        Parameters:
        x, y (int): The pivot point of the hook.
        length (int): The length of the hook's rope.
        swing_angle (float): The maximum swing angle (in degrees) from the resting point.
        speed (float): The speed of the swing.
        image (pygame.Surface): The optional image for the hook. Defaults to None.
        """
        self.pivot = pygame.Vector2(x, y)
        self.length = length
        self.swing_angle = swing_angle
        self.speed = speed
        self.image = image
        self.current_angle = 0
        self.direction = 1  # 1 for clockwise, -1 for counterclockwise
        self.swing_timer = 0
        self.hitbox = pygame.Rect(
            x - 5, y + length - 5, 40, 40
        )  # A small hitbox at the bottom of the rope

    def update(self, delta_time):
        """
        Updates the hook's position.

        Parameters:
        delta_time (float): Time since the last frame.
        """
        # Update the swing angle
        self.swing_timer += self.speed * delta_time * self.direction
        self.current_angle = math.sin(self.swing_timer) * self.swing_angle

        # Reverse direction if exceeding swing range
        if abs(self.current_angle) >= self.swing_angle:
            self.direction *= -1

        # Calculate the hook's swinging position
        radians = math.radians(self.current_angle)
        end_x = self.pivot.x + self.length * math.sin(radians)
        end_y = self.pivot.y + self.length * math.cos(radians)

        # Update the hitbox position
        self.hitbox.center = (end_x, end_y)

    def draw(self, camera, surface):
        """
        Draws the hook and its rope on the given surface, adjusted for the camera.

        Parameters:
        surface (pygame.Surface): The surface to draw on.
        camera (Camera): The camera object to adjust the rendering.
        """
        # Calculate hook position
        radians = math.radians(self.current_angle)
        end_x = self.pivot.x + self.length * math.sin(radians)
        end_y = self.pivot.y + self.length * math.cos(radians)

        # Apply camera transformations
        pivot_screen = camera.apply_point((self.pivot.x, self.pivot.y))
        end_screen = camera.apply_point((end_x, end_y))

        # Draw the rope
        pygame.draw.line(surface, (255, 255, 255), pivot_screen, end_screen, 2)

        # Draw the hook
        if self.image:
            hook_rect = self.image.get_rect(center=end_screen)
            surface.blit(self.image, hook_rect)
        else:
            pygame.draw.circle(surface, ("#17141a"), (int(end_screen[0]), int(end_screen[1])), 20)
