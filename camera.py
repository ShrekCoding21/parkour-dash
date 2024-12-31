import pygame
from Players.player import Player
from Platforms.platform import Platform
from artifacts import Artifact
from volcanoes import Volcano

class Camera:
    def __init__(self, width, height, window_size, zoom=1.0, max_zoom_out=0.8, zoom_speed=0.03, max_zoom_range=1.0):
        """
        Initializes the camera.

        :param width: The width of the game world.
        :param height: The height of the game world.
        :param window_size: The size of the display window.
        :param zoom: The initial zoom level of the camera.
        :param max_zoom_out: The minimum allowable zoom level.
        :param zoom_speed: The speed of smooth zooming.
        :param max_zoom_range: The maximum zoom level beyond which the camera won't zoom out.
        """
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.window_size = window_size
        self.zoom = zoom
        self.target_zoom = zoom  # For smooth zooming
        self.max_zoom_out = max(0.1, max_zoom_out)  # Prevent invalid max zoom-out levels
        self.zoom_speed = zoom_speed  # Determines how quickly zoom changes
        self.max_zoom_range = max_zoom_range  # Maximum zoom level threshold
        self.margin = 100
        self.is_active = True
        self.manual_mode = False  # Default to tracking mode
        self.manual_position = (0, 0)
        self.player_far_away = False  # Track if player is far away

    def apply(self, obj):
        """
        Transforms the given object's rectangle based on the camera's position and zoom.

        :param obj: The object to transform.
        :return: The transformed rectangle or dictionary of rectangles.
        """
        if isinstance(obj, Player):
            rect = obj.rect.copy()
            rect.x = (rect.x - self.camera_rect.x) * self.zoom
            rect.y = (rect.y - self.camera_rect.y) * self.zoom
            rect.width *= self.zoom
            rect.height *= self.zoom
            return rect

        elif isinstance(obj, Platform):
            return pygame.Rect(
                (obj.position.x - self.camera_rect.x) * self.zoom,
                (obj.position.y - self.camera_rect.y) * self.zoom,
                obj.dimensions[0] * self.zoom,
                obj.dimensions[1] * self.zoom
            )

        elif isinstance(obj, Artifact):
            rect = obj.rect.copy()
            rect.x = (rect.x - self.camera_rect.x) * self.zoom
            rect.y = (rect.y - self.camera_rect.y) * self.zoom
            rect.width *= self.zoom
            rect.height *= self.zoom
            return rect

        elif isinstance(obj, Volcano):
            base_rect = obj.volcano_rect.copy()
            base_rect.x = (base_rect.x - self.camera_rect.x) * self.zoom
            base_rect.y = (base_rect.y - self.camera_rect.y) * self.zoom
            base_rect.width *= self.zoom
            base_rect.height *= self.zoom

            steam_rect = obj.steam_rect.copy()
            steam_rect.x = (steam_rect.x - self.camera_rect.x) * self.zoom
            steam_rect.y = (steam_rect.y - self.camera_rect.y) * self.zoom
            steam_rect.width *= self.zoom
            steam_rect.height *= self.zoom

            cloud_rect = obj.cloud_rect.copy()
            cloud_rect.x = (cloud_rect.x - self.camera_rect.x) * self.zoom
            cloud_rect.y = (cloud_rect.y - self.camera_rect.y) * self.zoom
            cloud_rect.width *= self.zoom
            cloud_rect.height *= self.zoom

            return {"base": base_rect, "steam": steam_rect, "cloud": cloud_rect}

        return obj

    def update(self, player):
        """
        Updates the camera's position and zoom based on the mode.

        :param player: The player to track.
        """
        if self.manual_mode:
            # Use manual settings for position
            x, y = self.manual_position
            self.camera_rect.topleft = (
                max(0, min(x, self.width - self.window_size[0] / self.zoom)),
                max(0, min(y, self.height - self.window_size[1] / self.zoom))
            )
        else:
            if player:
                min_x = player.position.x - self.margin
                max_x = player.position.x + self.margin
                min_y = player.position.y - self.margin
                max_y = player.position.y + self.margin

                center_x = (min_x + max_x) / 2
                center_y = (min_y + max_y) / 2

                bounding_width = max_x - min_x
                bounding_height = max_y - min_y

                zoom_x = self.window_size[0] / bounding_width
                zoom_y = self.window_size[1] / bounding_height

                # Enforce the max_zoom_out limit
                self.target_zoom = max(min(zoom_x, zoom_y, 1.0), self.max_zoom_out)

                # Smoothly interpolate the zoom
                if abs(self.zoom - self.target_zoom) > 0.01:
                    self.zoom += (self.target_zoom - self.zoom) * self.zoom_speed
                else:
                    self.zoom = self.target_zoom

                if max_x - min_x > self.width / self.target_zoom * 2:  # Check if zoom-out needed
                    self.player_far_away = True
                else:
                    self.player_far_away = False

            # If far-away player respawns, zoom out temporarily
            if self.player_far_away and not self.manual_mode:
                self.zoom = max(self.max_zoom_out * 10, self.target_zoom)

                if self.zoom < self.max_zoom_range:
                    self.zoom += (self.max_zoom_range - self.zoom) * self.zoom_speed

            else:
                self.player_far_away = False

            camera_width = self.window_size[0] / self.zoom
            camera_height = self.window_size[1] / self.zoom
            self.camera_rect = pygame.Rect(
                max(0, min(center_x - camera_width / 2, self.width - camera_width)),
                max(0, min(center_y - camera_height / 2, self.height - camera_height)),
                camera_width,
                camera_height
            )

    def set_manual_mode(self, position=None, zoom=None):
        """
        Enables manual mode and optionally sets position and zoom.

        :param position: A tuple (x, y) for the camera's position.
        :param zoom: The zoom level to set.
        """
        self.manual_mode = True
        if position:
            self.manual_position = position
        if zoom:
            self.zoom = max(0.1, zoom)  # Prevent invalid zoom levels

    def set_tracking_mode(self):
        """
        Enables tracking mode.
        """
        self.manual_mode = False
