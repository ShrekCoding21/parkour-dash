import pygame
import asyncio
import json
import time
# from Player.player import Player
# from Platforms.platform import Platform

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

pygame.display.set_caption("Parkour Dash")

async def load_json_file(filepath):
    if WEB_ENVIRONMENT:
        # Load file using pygbag.fs in a web environment
        with pygbag.fs.open(filepath, 'r') as key_map:
            return json.load(key_map)
    else:
        # Load file normally in a local environment
        with open(filepath, 'r') as key_map:
            keys_data = json.load(key_map)
    return keys_data

class Player():


    def __init__(self, player_name, position, controls, color):
        super().__init__()
        self.player_name = player_name
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False
        self.on_platform = None
        self.jump_strength = 575
        self.speed = 125
        self.acceleration = 5000
        self.deceleration = 10000
        self.gravity = 50
        self.mass = 1
        # self.is_sliding = False
        self.controls = {action: getattr(pygame, key) for action, key in controls.items()}
        # self.animations = self.load_animations()
        # self.current_animation = self.animations["idle"]
        # self.shield = False
        # self.double_jump = False
        # self.effects = []
        # self.powerups = []

        "temp variables until we can add player sprites"

        self.width = 32
        self.height = 64
        self.color = color

    def names(self):

        player_names = []
        player_ids = []
        for id_num in range(2): 
            player_num = id_num + 1
            invalid = True

            while invalid:
                player_name = input(f"Player {player_num}, please enter your name")

                if player_name != '' and len(player_name) < 21:
                    if player_name not in player_names:
                        player_ids.append(f'player{player_num}')
                        player_names.append(player_name)
                        invalid = False
                    else:
                        print("That name is already being used, please choose a different one.")
                else:
                    print("Invalid name. Please choose a name smaller than 21 characters and not blank.")
      
        return player_names, player_ids
    
    def collisions(self, platforms):
        player_rect = self.rect
        self.on_ground = False
        tolerance = 5

        for platform in platforms:
            platform_rect = pygame.Rect(platform.position.x, platform.position.y, platform.dimensions[0], platform.dimensions[1])

            if player_rect.colliderect(platform_rect):
                overlap_x = min(player_rect.right - platform_rect.left, platform_rect.right - player_rect.left)
                overlap_y = min(player_rect.bottom - platform_rect.top, platform_rect.bottom - player_rect.top)

                if overlap_x < overlap_y:
                    
                    if self.velocity.x > 0:
                        self.position.x = platform_rect.left - self.width
                    
                    elif self.velocity.x < 0:
                        self.position.x = platform_rect.right
                    
                    else:
                        
                        if platform.direction.x == 1 and platform.previous_direction.x == 1:
                            self.position.x = platform_rect.right
                        
                        elif platform.direction.x == -1 and platform.previous_direction.x == -1:
                            self.position.x = platform_rect.left - self.width
                        
                    self.velocity.x = 0

                else:
                    
                    if self.velocity.y > 0: # player is falling
                        self.position.y = platform_rect.top - self.height
                        self.velocity.y = 0
                        self.on_ground = True
                        self.on_platform = platform
                    
                    elif self.velocity.y < 0 and platform_rect.bottom - player_rect.top <= tolerance: # player is jumping
                        self.position.y = platform_rect.bottom
                        self.velocity.y = 0

                player_rect = self.rect
    
    def load_animations(self):
        pass

    def update_animations(self):
        pass

    def momentum(self):
        return self.mass * self.velocity
    
    def jump(self):
        
        if self.on_ground:
            self.velocity.y = -self.jump_strength / self.mass
            self.on_ground = False

            if self.on_platform:
                self.on_platform = None

    def handle_controls(self, keys, delta_time):
        
        ACCELERATION = self.acceleration * delta_time
        DECELERATION = self.deceleration * delta_time

        if keys[self.controls['left']]:
            self.velocity.x -= ACCELERATION
        elif keys[self.controls['right']]:
            self.velocity.x += ACCELERATION
        else:
            
            if self.on_ground:
                if self.velocity.x > 0:
                    self.velocity.x = max(0, self.velocity.x - DECELERATION)
                elif self.velocity.x < 0:
                    self.velocity.x = min(0, self.velocity.x + DECELERATION)

        MAX_SPEED = self.speed
        self.velocity.x = max(-MAX_SPEED, min(MAX_SPEED, self.velocity.x))

        if keys[self.controls['jump']] and self.on_ground:
            self.jump()

    def update(self, delta_time, keys):

        self.gravity_and_motion(delta_time)
        self.handle_controls(keys, delta_time)

        if self.on_platform and self.on_platform.is_moving:
            self.position.x += self.on_platform.velocity.x * delta_time
        
        self.position += self.velocity * delta_time

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

    @property
    def rect(self):
        return pygame.Rect(self.position.x, self.position.y, self.width, self.height)

    def gravity_and_motion(self, delta_time):

        if not self.on_ground:
            self.velocity.y += self.gravity
            
        self.position.x += self.velocity.x * delta_time
        self.position.y += self.velocity.y * delta_time

    def reload(self, position):
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False

import pygame

class Platform():
    

    def __init__(self, position, image, is_moving, movement_range, speed, direction, image_path, dimensions, color):

        self.start_position = pygame.Vector2(position)
        self.position = pygame.Vector2(position)
        self.is_moving = is_moving
        self.movement_range = pygame.Vector2(movement_range)
        self.speed = speed
        self.animation_frames = []
        self.current_frame = 0
        self.frame_count = len(self.animation_frames)
        self.direction = pygame.Vector2(direction)
        self.previous_direction = self.direction.copy()
        self.image_path = image_path
        self.image = image
        self.color = color
        self.dimensions = dimensions
        self.velocity = pygame.Vector2(0, 0)

    def update(self, dt):
        if self.is_moving:
            self.velocity = self.direction * self.speed
            self.previous_direction = self.direction.copy()
            self.position += self.direction * self.speed * dt
            if self.position.distance_to(self.start_position) > self.movement_range.length():
                self.direction *= -1
        if self.frame_count > 0:    
            self.current_frame = (self.current_frame + 1) % self.frame_count

    def draw(self, screen):
        if self.animation_frames:
            frame = self.animation_frames[self.current_frame]
            screen.blit(frame, self.position)
        else:
            if self.is_moving:
                pygame.draw.rect(screen, self.color, (*self.position, self.dimensions[0], self.dimensions[1]))
    
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

    
def load_platforms(platform_data, level_name):

    platforms = []
    level_data = platform_data['platforms']['levels'][level_name]

    for platform_name, platform_data in level_data.items():
        platform_dimensions = (platform_data['width'], platform_data['height'])
        platform_position = (platform_data['x-position'], platform_data['y-position'])
        platform_direction = (platform_data['x-direction'], platform_data['y-direction'])
        platform_movement_range = (platform_data['x-movement_range'], platform_data['y-movement_range'])

        platform = Platform(
            position=platform_position,
            is_moving = platform_data['is_moving'],
            image_path=platform_data['image_path'],
            dimensions=platform_dimensions,
            speed=platform_data['speed'],
            direction=platform_direction,
            image=platform_data['image'],
            movement_range=platform_movement_range,
            color = platform_data['color']
        )
            
        platforms.append(platform)

    return platforms

class Powerups():
    pass

def pause_game(screen, clock, window_size):

    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 55)
    text = font.render('Paused', True, ('#399cd4b9'))
    text_rect = text.get_rect(center=(window_size[0] // 2, window_size[1] // 2))
        
    screen.blit(text, text_rect)
    pygame.display.flip()

    clock.tick(10)

def reload_players(players, platforms, reset_positions):
        
        for platform in platforms:
            platform.reset()

        for player, position in zip(players, reset_positions):
            player.reload(position)


async def main():

    keys_data = await load_json_file('player_controls.json')
    platforms_data = await load_json_file('platforms.json')

    player1_controls = keys_data['controls']['players']['player1']
    player2_controls = keys_data['controls']['players']['player2']

    level_name = 'demo_level'
    platforms = load_platforms(platforms_data, level_name)

    player1 = Player(player_name="Player 1", position=(100, 100), controls=player1_controls, color=("#9EBA01"))
    player2 = Player(player_name="Player 2", position=(200, 100), controls=player2_controls, color=("#1D01BA"))

    players = [player1, player2]
    reset_positions = [(100, 100), (200, 100)]

    running = True
    paused = False

    while running:
        dt = clock.tick(60) / 1000.0
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_r:
                    reload_players(players, platforms, reset_positions)
                elif event.key == pygame.K_ESCAPE:
                    paused = True
                elif paused and event.key == pygame.K_RETURN:
                    paused = False

        if paused:

            pause_game(screen, clock, window_size)

        if not paused:
            
            for platform in platforms:
                platform.update(dt)

            for player in players:
                player.update(dt, keys)
                player.collisions(platforms)

            screen.fill((0, 0, 0))
            
            for platform in platforms:
                platform.draw(screen)

            for player in players:
                player.draw(screen)

            pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()

# Run the main function
asyncio.run(main())

"""if you read this you are nice"""
