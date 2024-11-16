import pygame
import asyncio
import json
import datetime
from Player.player import Player

WEB_ENVIRONMENT = False
try:
    import pygbag.fs # type: ignore
    WEB_ENVIRONMENT = True
except ImportError:
    pass  # We're not running in a web environment

pygame.init()
window_size = (800, 600)
screen = pygame.display.set_mode(window_size)
clock = pygame.time.Clock()

pygame.display.set_caption("Karthikeya Abhimanyu Ainapurapu")

async def load_json_file(filepath):
    if WEB_ENVIRONMENT:
        # Load file using pygbag.fs in a web environment
        with pygbag.fs.open(filepath, 'r') as key_map:
            keys_data = json.load(key_map)
    else:
        # Load file normally in a local environment
        with open(filepath, 'r') as key_map:
            keys_data = json.load(key_map)
    return keys_data

class Platform():
    

    def __init__(self, position, image, is_moving, movement_range, speed, direction, image_path, width, height):

        self.start_position = pygame.Vector2(position)
        self.position = pygame.Vector2(position)
        self.is_moving = is_moving
        self.movement_range = pygame.Vector2(movement_range)
        self.speed = speed
        self.animation_frames = []
        self.current_frame = 0
        self.frame_count = len(self.animation_frames)
        self.direction = direction
        self.image_path = image_path
        self.image = image
        self.color = (156, 185, 39)
        self.width, self.height = width, height

    def update(self, dt):
        if self.is_moving:
            self.posiiton += self.direction * self.speed * dt
            if self.position.distance_to(self.start_position) > self.movement_range.length():
                self.direction *= 1
            self.current_frame = (self.current_frame + 1) % self.frame_count
    def draw(self, screen):
        if self.animation_frames:
            frame = self.animation_frames[self.current_frame]
            screen.blit(frame, self.position)
        else:
            pygame.draw.rect(screen, self.color, (*self.position, self.width, self.height))
    
    def set_image(self, image_path):
        if image_path is not None:
            image = pygame.image.load(image_path)
            self.animation_frames = [image]
            self.frame_count = len(self.animation_frames)
        else:
            self.animation_frames = []
            self.frame_count = 0

    
    def set_animation_frames(self, image_paths):
        self.animation_frames = [pygame.image.load(path) for path in image_paths]
        frame_count = len(self.animation_frames)

    def reset(self):
        self.position = pygame.Vector2(self.start_position)
        self.current_frame = 0
    


    

class Powerups():
    pass

async def main():

    keys_data = await load_json_file('player/player_controls.json')

    player1_controls = keys_data['controls']['players']['player1']
    player2_controls = keys_data['controls']['players']['player2']

    platform = Platform(position=(100, 400), is_moving = False, image_path=None, width=200, height=50, speed=100, direction=pygame.Vector2(1, 0), image=None, movement_range=pygame.Vector2(300, 0))
    player1 = Player(player_name="Player 1", position=(100, 100), controls=player1_controls, color=(0, 255, 0))
    player2 = Player(player_name="Player 2", position=(200, 100), controls=player2_controls, color=(0, 0, 255))

    platforms = [platform]

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        dt = clock.get_time() / 1000.0
        platform.update(dt)

        player1.update(dt, keys)
        player1.collisions(platforms)
        player2.update(dt, keys)
        player2.collisions(platforms)

        screen.fill((0, 0, 0))
        platform.draw(screen)
        player1.draw(screen)
        player2.draw(screen)
        pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()

# Run the main function
asyncio.run(main())

"""if you read this you are gay"""
