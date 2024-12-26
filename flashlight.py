import pygame
import math

class Flashlight:
    def __init__(self, screen, radius=250, intensity=100, beam_width=75, flipped=False):
        self.screen = screen
        self.radius = radius
        self.intensity = intensity
        self.beam_width = beam_width
        self.on = False
        self.pos = pygame.Vector2(screen.get_width() // 2, screen.get_height() // 2)
        self.flipped = flipped 

        # Create a pre-rendered gradient
        self.gradient_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.gradient_surface.fill((0, 0, 0, 0))
        for x in range(self.radius * 2):
            for y in range(self.radius * 2):
                dist = ((x - self.radius) ** 2 + (y - self.radius) ** 2) ** 0.5
                if dist <= self.radius:
                    intensity = (self.intensity * (1 - dist / self.radius))
                    color = (255, 255, 0, intensity)  # Yellow color
                    self.gradient_surface.set_at((x, y), color)

    def draw(self, camera):
        # Transform flashlight position based on the camera
        adjusted_pos = pygame.Vector2(
            (self.pos[0] - camera.camera_rect.x) * camera.zoom,
            (self.pos[1] - camera.camera_rect.y) * camera.zoom
        )

        # Adjust beam size for the current zoom
        scaled_radius = int(self.radius * camera.zoom)
        scaled_gradient = pygame.transform.scale(
            self.gradient_surface,
            (scaled_radius * 2, scaled_radius * 2)
        )

        # Create the beam
        beam_surface = pygame.Surface((scaled_radius * 2, scaled_radius * 2), pygame.SRCALPHA)
        beam_surface.fill((0, 0, 0, 0))

        mask_surface = pygame.Surface((scaled_radius * 2, scaled_radius * 2), pygame.SRCALPHA)
        mask_surface.fill((0, 0, 0, 0))
        pygame.draw.arc(
            mask_surface,
            (255, 255, 255, 255),
            (0, 0, scaled_radius * 2, scaled_radius * 2),
            math.radians(-self.beam_width / 2),  # Start arc at -beam_width/2
            math.radians(self.beam_width / 2),  # End arc at beam_width/2
            scaled_radius
        )

        beam_surface.blit(scaled_gradient, (0, 0))
        beam_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Flip the beam if needed
        if self.flipped:
            beam_surface = pygame.transform.flip(beam_surface, True, False) 

        # Calculate offset for centered drawing
        offset_x = beam_surface.get_width() // 2
        offset_y = beam_surface.get_height() // 2

        # Store the rotated beam 
        self.rotated_beam = beam_surface 

        # Draw the beam on the screen
        self.screen.blit(beam_surface, (adjusted_pos[0] - offset_x, adjusted_pos[1] - offset_y))