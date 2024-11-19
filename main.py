import pygame
import asyncio
import json
import time
from Player.player import Player
from Platforms.platform import Platform

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
            return json.load(key_map)
    else:
        # Load file normally in a local environment
        with open(filepath, 'r') as key_map:
            keys_data = json.load(key_map)
    return keys_data
    
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

async def main():

    keys_data = await load_json_file('player/player_controls.json')
    platforms_data = await load_json_file('Platforms/platforms.json')

    player1_controls = keys_data['controls']['players']['player1']
    player2_controls = keys_data['controls']['players']['player2']

    level_name = 'demo_level'
    platforms = load_platforms(platforms_data, level_name)

    player1 = Player(player_name="Player 1", position=(100, 100), controls=player1_controls, color=("#9EBA01"))
    player2 = Player(player_name="Player 2", position=(200, 100), controls=player2_controls, color=("#1D01BA"))

    def reload_players():
            platform.reset()
            player1.reload(position=(100, 100))
            player2.reload(position=(200, 100))
        
    def pause_game():
        nonlocal paused
        pause = True

        player1_saved_momentum = player1.momentum
        player2_saved_momentum = player2.momentum

        while pause:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

                elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    pause = False

            font = pygame.font.SysFont(None, 55)
            text = font.render('Paused', True, (35, 35, 35))
            screen.blit(text, (window_size[0]//2 - text.get_width()//2, window_size[1]//2 - text.get_height()//2))
            pygame.display.flip()

            clock.tick(10)

        player1.momentum = player1_saved_momentum
        player2.momentum = player2_saved_momentum


    running = True
    paused = False

    while running:
        dt = clock.tick(60) / 1000.0
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif keys[pygame.K_r]:
                reload_players()

            elif keys[pygame.K_ESCAPE]:
                paused = True

        if paused:
            pause_game()
            paused = False

        if not paused:
            for platform in platforms:
                platform.update(dt)

            player1.update(dt, keys)
            player1.collisions(platforms)

            player2.update(dt, keys)
            player2.collisions(platforms)

            screen.fill((0, 0, 0))
            for platform in platforms:
                platform.draw(screen)

            player1.draw(screen)
            player2.draw(screen)
            pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()

# Run the main function
asyncio.run(main())

"""if you read this you are nice"""
