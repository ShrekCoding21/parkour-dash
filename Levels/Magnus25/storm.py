import pygame
import random

class Storm:
    def __init__(self, trigger_distance, platforms, font, screen_size):
        """
        Initializes the Storm object.

        Parameters:
        trigger_distance (float): The distance from the platform to trigger the storm.
        platform (Platform): The platform to use as shelter.
        font (pygame.font.Font): Font for displaying text.
        screen_size (tuple): Size of the game screen (width, height).
        """
        self.trigger_distance = trigger_distance
        self.platforms = platforms
        self.trigger_platform = None
        self.disarmed = False
        self.disarm_distance = 400
        self.font = font
        self.screen_size = screen_size
        self.active = False
        self.warning = False
        self.critical_warning = False
        self.storm_start_time = None
        self.storm_duration = random.uniform(5, 10)
        self.player_last_checkpoint = None
        self.warning_start_time = None

    def update(self, player, spawnpoint, current_time):
        """
        Updates the storm's state.

        Parameters:
        player (Player): The player object.
        current_time (float): Current time in seconds.
        """

        if self.disarmed:
            if abs(self.trigger_platform.rect.centerx - player.rect.centerx) >= self.disarm_distance:
                self.trigger_platform = None
                self.disarmed = False
        
        else:
            # Check distance to trigger the warning phase
            for platform in self.platforms:
                player_distance = abs(platform.rect.centerx - player.rect.centerx)
                if player_distance <= self.trigger_distance and not self.warning and not self.active:
                    self.trigger_platform = platform
                    print(self.trigger_platform)
                    self.warning = True
                    self.warning_start_time = current_time

            # Activate the storm after the warning phase
            if self.warning and not self.active:
                if current_time - self.warning_start_time >= 2.5:
                    self.critical_warning = True
                if current_time - self.warning_start_time >= 5:  # Warning lasts for 5 seconds
                    self.active = True
                    self.storm_start_time = current_time

            # End the storm after its duration
            if self.active and current_time - self.storm_start_time >= self.storm_duration:
                self.disarmed = True
                self.reset()

            # Check if the player is on the platform during the storm
            if self.active and not player.on_platform == self.trigger_platform:
                print(self.trigger_platform)
                print(player.on_platform)
                print("Player failed to seek shelter!")
                player.reload(spawnpoint)
                self.reset()

    def reset(self):
        """Resets the storm state."""
        self.active = False
        self.warning = False
        self.critical_warning = False
        self.storm_start_time = None
        self.storm_duration = random.uniform(5, 10)
        self.warning_start_time = None

    def draw(self, surface):
        """
        Draws the storm visuals and warning text.

        Parameters:
        surface (pygame.Surface): The game surface to draw on.
        """
        if self.warning:
            # Draw a translucent red hue for the warning phase
            overlay = pygame.Surface((1000, 700), pygame.SRCALPHA)
            overlay.fill((219, 104, 33, 80))  # Light red with some transparency
            surface.blit(overlay, (0, 0))
        
        if self.critical_warning:
            overlay = pygame.Surface((1000, 700), pygame.SRCALPHA)
            overlay.fill((209, 60, 38, 90))  # Mid red with some more transparency
            surface.blit(overlay, (0, 0))

            # Display the warning message
            warning_text = self.font.render("Get Inside!", True, (255, 255, 255))
            surface.blit(
                warning_text,
                (self.screen_size[0] // 2 - warning_text.get_width() // 2, 50)
            )

        if self.active:
            overlay = pygame.Surface((1000, 700), pygame.SRCALPHA)
            overlay.fill((250, 46, 5, 100))  # Dark red with even less transparency
            surface.blit(overlay, (0, 0))
