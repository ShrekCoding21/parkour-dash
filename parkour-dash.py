import pygame
import asyncio
import json
import time
from Players.player import Player
from Platforms.platform import Platform

WEB_ENVIRONMENT = False
try:
    import pygbag.fs # type: ignore
    WEB_ENVIRONMENT = True
except ImportError:
    pass  # We're not running in a web environment

pygame.init()
window_size = (1000, 700)
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
            movement_range=platform_movement_range,
            color = platform_data['color']
        )
            
        platforms.append(platform)

    return platforms

class Powerups():
    pass

def freeze_game(screen, clock, window_size, paused, game_finished, best_player, text_color):

    if paused:
        text1 = "Paused"
        text2 = None
        f_size = 55

    if game_finished:
        text1 = f'player {best_player} wins!'
        text2 = 'press (r) to restart game'
        f_size = 35

    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', f_size)
    texts = [text1, text2]
    
    

    offset = 30

    for text in texts:        
        printtext = font.render(text, True, (text_color))
        text_rect = printtext.get_rect(center=(window_size[0] // 2, window_size[1] // 2 - offset))
        screen.blit(printtext, text_rect)
        offset = -offset

    pygame.display.flip()

    clock.tick(10)


def reload_players(players, platforms, reset_positions):
        
        for platform in platforms:
            platform.reset()

        for player, position in zip(players, reset_positions):
            player.reload(position)

def display_controls():
       
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 25)

    p1_controls = [
        'a: left',
        'd: right',
        'w: jump'
        ]
    
    p2_controls = [
        'left-arrow: left',
        'right-arrow: right',
        'up-arrow: up'
        ]
    
    general_controls = [
        'p: game pause',
        'u: game unpause',
        'r: game reload'
        ]

    x_position = 20
    vertical_displacement = 150
    for p1_control in p1_controls:
        print_p1_controls = font.render(p1_control, True, ("#9EBA01"))
        p1_control_rect = print_p1_controls.get_rect(topleft=(x_position, vertical_displacement))
        screen.blit(print_p1_controls, p1_control_rect)
        vertical_displacement += 30

    for p2_control in p2_controls:
        print_p2_controls = font.render(p2_control, True, ("#2276c9"))
        p2_control_rect = print_p2_controls.get_rect(topleft=(x_position, vertical_displacement))
        screen.blit(print_p2_controls, p2_control_rect)
        vertical_displacement += 30

    x_position = 990
    vertical_displacement = 10
    for general_control in general_controls:
        print_general_controls = font.render(general_control, True, ("#ffffff"))
        general_control_rect = print_general_controls.get_rect(topright=(x_position, vertical_displacement))
        screen.blit(print_general_controls, general_control_rect)
        vertical_displacement += 30
            
def update_game_logic(delta_time, players, platforms, keys):

    for player in players:
        player.update(delta_time, keys)
        player.collisions(platforms)

    for platform in platforms:
        platform.update(delta_time)


async def main():

    keys_data = await load_json_file('Players/player_controls.json')
    platforms_data = await load_json_file('Platforms/platforms.json')

    player1_controls = keys_data['controls']['players']['player1']
    player2_controls = keys_data['controls']['players']['player2']

    level_name = 'demo_level'
    platforms = load_platforms(platforms_data, level_name)

    player1 = Player(player_id=1, position=(910, 610), controls=player1_controls, color=("#9EBA01"))
    player2 = Player(player_id=2, position=(910, 610), controls=player2_controls, color=("#2276c9"))

    players = [player1, player2]
    reset_positions = [(910, 610), (910, 610)]

    running = True
    fixed_delta_time = 1 / 60
    accumulator = 0
    paused = False
    finish_line = None
    game_finished = False
    best_player = None
    text_color = ("#71d6f5")

    for platform in platforms:
        if platform.position == pygame.Vector2(30, 100):
            finish_line = platform

    while running:
        dt = clock.tick(60) / 1000.0
        accumulator += dt
        keys = pygame.key.get_pressed()

        for player in players:

            if player.position.y > 800:
                player.reload(position=(910, 610))

            if player.on_platform == finish_line:
                best_player = player.id
                game_finished = True
                text_color = player.color

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_r:
                    reload_players(players, platforms, reset_positions)
                    best_player = None
                    game_finished = False
                    text_color = ("#71d6f5")
                
                if event.key == pygame.K_p:
                    paused = True
                
                elif paused or game_finished:

                    if event.key == pygame.K_u:
                        paused = False
                    
                    elif event.key == pygame.K_r:
                        reload_players(players, platforms, reset_positions)
                        paused = False
                        game_finished = False
                        best_player = None
                        text_color = ("#71d6f5")

        if paused or game_finished:

            freeze_game(screen, clock, window_size, paused, game_finished, best_player, text_color)

        if not paused and not game_finished:

            while accumulator >= fixed_delta_time:
                update_game_logic(fixed_delta_time, players, platforms, keys)
                accumulator -= fixed_delta_time

            screen.fill((0, 0, 0))
            
            for platform in platforms:
                platform.draw(screen)

            for player in players:
                player.draw(screen)

            display_controls()

            pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()

# Run the main function
asyncio.run(main())

"""if you read this you are nice"""