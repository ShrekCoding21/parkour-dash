import pygame
import json

class Spritesheet:
    def __init__(self, filename, width, height):
        self.filename = filename
        self.target_width = width
        self.target_height = height
        
        try:
            self.sprite_sheet = pygame.image.load(filename).convert_alpha()
        except pygame.error as e:
            print(f"Error loading sprite sheet: {e}")
            raise
        
        self.meta_data = self.filename.replace('png', 'json')
        try:
            with open(self.meta_data) as f:
                self.data = json.load(f)
        except FileNotFoundError:
            print(f"Error: {self.meta_data} not found!")
            raise

    def get_sprite(self, x, y, w, h):
        sprite = pygame.Surface((w, h), pygame.SRCALPHA)
        sprite.blit(self.sprite_sheet, (0, 0), (x, y, w, h))
        # Scale the sprite to the target dimensions
        scaled_sprite = pygame.transform.scale(sprite, (self.target_width, self.target_height))
        return scaled_sprite

    def get_all_frames(self, name):
        try:
            frame_data = self.data['frames'][name]
            total_frames = frame_data['total_frames']
            frame_info = frame_data['frame']
        except KeyError:
            print(f"Error: {name} not found in JSON.")
            return [], 0

        frame_w, frame_h = frame_info["w"], frame_info["h"]
        frames = []

        for i in range(total_frames):
            x = frame_info["x"] + i * frame_w
            y = frame_info["y"]
            frames.append(self.get_sprite(x, y, frame_w, frame_h))
        
        frame_speed = self.data['frames'][name]['animation_speed']

        return frames, total_frames, frame_speed