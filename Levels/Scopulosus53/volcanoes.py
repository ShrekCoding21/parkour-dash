import pygame
import random
import time
from sprites import Spritesheet

class Volcano:
    def __init__(self, name, position, steam_height, steam_correction, screen, stretch_size=(1400, 500)):
        """
        Initializes the Volcano.

        :param position: A tuple (x, y) representing the volcano's position.
        :param screen: The screen surface where the volcano will be drawn.
        :param stretch_size: A tuple (width, height) specifying the size to stretch the volcano image.
        """
        self.name = name
        self.position = position
        self.screen = screen
        self.stretch_size = stretch_size

        # Load and stretch the volcano image
        self.original_volcano_image = pygame.image.load("Levels/Scopulosus53/assets/volcano.png").convert_alpha()
        self.volcano_image = pygame.transform.scale(self.original_volcano_image, (self.stretch_size))

        # Create the rectangle for the volcano
        self.volcano_rect = self.volcano_image.get_rect(topleft=self.position)

        # Create the steam rectangle
        self.steam_correction = steam_correction
        self.steam_rect, self.cloud_rect = self.create_steam_rect(steam_height)

        # Initialize spritesheets for steam and cloud animations
        self.steam_spritesheet = Spritesheet("Levels/Scopulosus53/assets/steam.png", self.steam_rect.width, steam_height)
        self.steam_frames, self.total_steam_frames, self.frame_speed = self.steam_spritesheet.get_all_frames("steam.png")

        self.cloud_spritesheet = Spritesheet("Levels/Scopulosus53/assets/cloud.png", self.cloud_rect.width, int(self.cloud_rect.width * (230 / 500)))
        self.cloud_frames, self.total_cloud_frames, self.cloud_frame_speed = self.cloud_spritesheet.get_all_frames("cloud.png")

        self.current_steam_frame = 0
        self.current_cloud_frame = 0

        # Timing for animation
        self.steam_push_force = 3000
        self.steam_active = False
        self.last_toggle_time = time.time()
        self.next_toggle_delay = self._calculate_next_toggle_delay()
        self.last_frame_time = 0
        self.last_cloud_frame_time = 0
        self.interacting_with_player = False

    def create_steam_rect(self, height):
        """
        Creates the steam rectangle as a narrow section in the middle of the volcano.
        """
        steam_width = self.volcano_rect.width * 0.1
        steam_height = height
        steam_x = self.volcano_rect.centerx - (steam_width / 2) + self.steam_correction
        steam_y = self.volcano_rect.top - steam_height + 50

        cloud_width = steam_width * 0.85
        cloud_height = cloud_width * 0.46
        cloud_x = steam_x - (cloud_width / 2) + self.steam_correction + 36
        cloud_y = steam_y - cloud_height + 5

        return pygame.Rect(steam_x, steam_y, steam_width, steam_height), pygame.Rect(cloud_x, cloud_y, cloud_width, cloud_height)


    def _calculate_next_toggle_delay(self):
        """Calculate the next delay for toggling steam on/off."""
        return random.uniform(3, 6)

    def update(self):
        """Updates the state of the steam and cloud animations."""
        # Toggle steam state
        current_time = time.time()
        if current_time - self.last_toggle_time >= self.next_toggle_delay:
            self.steam_active = not self.steam_active
            self.last_toggle_time = current_time
            self.next_toggle_delay = self._calculate_next_toggle_delay()

        # Update steam animation
        if self.steam_active and self.total_steam_frames > 0:
            if current_time - self.last_frame_time >= self.frame_speed / 1000:  # Convert ms to s
                self.current_steam_frame = (self.current_steam_frame + 1) % self.total_steam_frames
                self.last_frame_time = current_time

        # Update cloud animation
        if self.steam_active and self.total_cloud_frames > 0:
            if current_time - self.last_cloud_frame_time >= self.cloud_frame_speed / 1000:
                self.current_cloud_frame = (self.current_cloud_frame + 1) % self.total_cloud_frames
                self.last_cloud_frame_time = current_time

    def draw(self, camera, screen):
        """Draws the volcano, steam, and cloud on the specified screen."""
        transformed_rects = camera.apply(self)
        if transformed_rects:
            # Draw steam animation
            if self.steam_active:
                steam_image = self.steam_frames[self.current_steam_frame]
                screen.blit(steam_image, transformed_rects["steam"].topleft)

                # Draw cloud animation
                cloud_image = self.cloud_frames[self.current_cloud_frame]
                screen.blit(cloud_image, transformed_rects["cloud"].topleft)

            # Draw volcano image
            screen.blit(self.volcano_image, transformed_rects["base"].topleft)

    def interact_with_player(self, player, volcanoes):
        """
        Handles interaction with the player.

        :param player: The player object to interact with.
        """
        if self.steam_active and self.steam_rect.colliderect(player.rect):
            # If the player is within this volcano's steam area, apply effects
            player.mass = 0.5
            player.acceleration = 20000
            player.speed = 100
            player.velocity.y = max(player.velocity.y - 1, -self.steam_push_force)
            player.gravity = -10  # Temporary reduced gravity when in steam
            self.interacting_with_player = True
        else:
            self.interacting_with_player = False
            all_volcanoes_not_interacting = all(not volcano.interacting_with_player for volcano in volcanoes if volcano != self) 
            if all_volcanoes_not_interacting:
                # Reset player properties if they are not interacting with any volcanoes
                player.gravity = 50
                player.acceleration = 5000
                player.speed = 200
                player.mass = 1


