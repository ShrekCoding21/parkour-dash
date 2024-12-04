import pygame
import asyncio
import json
import time
from Players.player import Player
from Platforms.platform import Platform
from camera import Camera

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

"""copy changes below this line into main.py"""

def load_platforms(platform_data, level_name):

    platforms = []
    platform_names = []
    level_data = platform_data[level_name]['platforms']
    platform_names = list(level_data.keys())
    list_item = 0

    for platform_name, platform_data in level_data.items():
        platform_dimensions = (platform_data['width'], platform_data['height'])
        platform_position = (platform_data['x-position'], platform_data['y-position'])
        
        if platform_data['is_moving'] == 'True':
            platform_speed = platform_data['speed']
            platform_direction = (platform_data['x-direction'], platform_data['y-direction'])
            platform_movement_range = (platform_data['x-movement_range'], platform_data['y-movement_range'])

        else:
            platform_speed, platform_direction, platform_movement_range = 0, (0, 0), (0, 0)

        if 'image_path' in platform_data:
            platform_image_path = platform_data['image_path']
        
        else:
            platform_image_path = None
            

        

        platform = Platform(
            name = platform_names[list_item],
            position = platform_position,
            is_moving = platform_data['is_moving'],
            image_path = platform_image_path,
            dimensions = platform_dimensions,
            speed = platform_speed,
            direction = platform_direction,
            movement_range = platform_movement_range,
            color = platform_data['color']
        )
 
        platforms.append(platform)
        list_item += 1


    return platforms

def freeze_game(screen, clock, window_size, counting_string, paused, game_finished, best_player_num, text_color):

    if paused:
        text1 = "Paused"
        text2 = None
        text3 = None
        f_size = 55

    if game_finished:
        text1 = f'player {best_player_num} wins!'
        text2 = 'press (r) to restart game'
        text3 = f'completion time: {counting_string}'
        f_size = 35

    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', f_size)
    texts = [text1, text2, text3]
    offset = 30

    for text in texts:        
        printtext = font.render(text, True, (text_color))
        text_rect = printtext.get_rect(center=(window_size[0] // 2, window_size[1] // 2 - offset))
        screen.blit(printtext, text_rect)
        offset -= 60

    pygame.display.flip()

    clock.tick(10)


def reload_map(active_players, platforms, reset_positions):
        
        for platform in platforms:
            platform.reset()

        for player, position in zip(active_players, reset_positions):
            player.reload(position)

def display_controls(introduced_controls_state, counting_string, print_player1_controls, print_player2_controls, print_player3_controls, print_player4_controls, p2_active, p3_active, p4_active, timer_color):
    
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 25)
    
    full_p1_controls = print_player1_controls
    full_p2_controls = print_player2_controls
    full_p3_controls = print_player3_controls
    full_p4_controls = print_player4_controls

    if not introduced_controls_state["introduced_jumping"]:
        
        p1_controls = [full_p1_controls[0], full_p1_controls[1]]
        
        if p4_active:
            p2_controls = [full_p2_controls[0], full_p2_controls[1]]
            p3_controls = [full_p3_controls[0], full_p3_controls[1]]
            p4_controls = [full_p4_controls[0], full_p4_controls[1]]

        elif p3_active and not p4_active:
            p3_controls = [full_p3_controls[0], full_p3_controls[1]]
            p2_controls = [full_p2_controls[0], full_p2_controls[1]]

        elif p2_active and not p3_active:
            p2_controls = [full_p2_controls[0], full_p2_controls[1]]


    
    elif not introduced_controls_state["introduced_sliding"] and introduced_controls_state["introduced_jumping"]:

        p1_controls = [full_p1_controls[0], full_p1_controls[1], full_p1_controls[2]]
        
        if p4_active:
            p2_controls = [full_p2_controls[0], full_p2_controls[1], full_p2_controls[2]]
            p3_controls = [full_p3_controls[0], full_p3_controls[1], full_p3_controls[2]]
            p4_controls = [full_p4_controls[0], full_p4_controls[1], full_p4_controls[2]]
        
        elif p3_active and not p4_active:
            p2_controls = [full_p2_controls[0], full_p2_controls[1], full_p2_controls[2]]
            p3_controls = [full_p3_controls[0], full_p3_controls[1], full_p3_controls[2]]

        elif p2_active and not p3_active:
            p2_controls = [full_p2_controls[0], full_p2_controls[1], full_p2_controls[2]]          
        
    else:

        p1_controls = full_p1_controls       
        
        if p4_active:
            p2_controls = full_p2_controls       
            p3_controls = full_p3_controls
            p4_controls = full_p4_controls

        elif p3_active and not p4_active:
            p2_controls = full_p2_controls       
            p3_controls = full_p3_controls

        elif p2_active and not p3_active:
            p2_controls = full_p2_controls
    
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
    
    if p2_active:

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

    print_timer = font.render(counting_string, True, (timer_color))
    timer_rect = print_timer.get_rect(topright=(x_position, vertical_displacement))
    screen.blit(print_timer, timer_rect)

    vertical_displacement = 450

    if p3_active:

        for p3_control in p3_controls:
            print_p3_controls = font.render(p3_control, True, ("#c7b61a"))
            p3_control_rect = print_p3_controls.get_rect(topright=(x_position, vertical_displacement))
            screen.blit(print_p3_controls, p3_control_rect)
            vertical_displacement += 30

    if p4_active:

        for p4_control in p4_controls:
            print_p4_controls = font.render(p4_control, True, ("#c7281a"))
            p4_control_rect = print_p4_controls.get_rect(topright=(x_position, vertical_displacement))
            screen.blit(print_p4_controls, p4_control_rect)
            vertical_displacement += 30

def determine_blitted_controls(active_players, p1_controls, p3_controls, p4_controls):

    print_player1_controls = []
    print_player2_controls = []
    print_player3_controls = []
    print_player4_controls = []

    p2_active = False
    p3_active = False
    p4_active = False

    for action, key in p1_controls.items():
        print_player1_controls.append(f'{action}: {key}')

    if len(active_players) >= 4:    
        p4_active = True
        p3_active = True
        p2_active = True
        
        for action, key in p4_controls.items():
            print_player4_controls.append(f'{action}: {key}')

        for action, key in p3_controls.items():
            print_player3_controls.append(f'{action}: {key}')

        print_player2_controls = [
            '←: left',
            '→: right',
            '↑: jump',
            '↓: slide'
        ]

    elif len(active_players) >= 3 and not p4_active:
        p3_active = True
        p2_active = True

        for action, key in p3_controls.items():
            print_player3_controls.append(f'{action}: {key}')

        print_player2_controls = [
            '←: left',
            '→: right',
            '↑: jump',
            '↓: slide'
        ]

    elif len(active_players) >= 2 and not p3_active:
        p2_active = True
        print_player2_controls = [
            '←: left',
            '→: right',
            '↑: jump',
            '↓: slide'
        ]

    return print_player1_controls, print_player2_controls, print_player3_controls, print_player4_controls, p2_active, p3_active, p4_active
            
def update_game_logic(delta_time, active_players, platforms, keys, position):

    for player in active_players:
        player.update(delta_time, keys, platforms, position)
        player.collisions(platforms)

    for platform in platforms:
        platform.update(delta_time)

def update_timer(start_timer):
    
    counting_time = pygame.time.get_ticks() - start_timer
    counting_minutes = counting_time // 60000  # Minutes
    counting_seconds = (counting_time % 60000) // 1000  # Seconds
    counting_milliseconds = (counting_time % 1000) // 10
    counting_string = f"{counting_minutes:02d}:{counting_seconds:02d}:{counting_milliseconds:02d}"

    return counting_string

def get_special_platforms(platforms, level_name):

    next_checkpoints = list()
    deathforms = list()
    checkpoint_num = 1
    deathpoint_num = 1

    for platform in platforms:

        if platform.name == "starting-platform":
            spawn_point = (platform.position.x + (platform.dimensions[0] / 2), platform.position.y - platform.dimensions[1])

        if platform.name == f"checkpoint{checkpoint_num}":
            next_checkpoints.append(platform)
            checkpoint_num += 1

        if platform.name == "finish-line":
            finish_line = platform

        if level_name == "tutorial_level":
            
            if platform.name == "introduce-jumping":
                intro_to_jumping = platform

            if platform.name == "introduce-sliding":
                intro_to_sliding = platform

            if platform.name == f"death-form{deathpoint_num}":
                deathforms.append(platform)
                deathpoint_num += 1
        
        else:
            intro_to_jumping, intro_to_sliding = None, None

    return spawn_point, intro_to_jumping, intro_to_sliding, deathforms, next_checkpoints, finish_line

def render_game_objects(platforms, active_players, camera):

    for platform in platforms:
        
        platform_rect = camera.apply(platform)
                
        if platform.image:  # If the platform has an image
            
            scaled_image = pygame.transform.scale(
                platform.image,
                (int(platform_rect.width), int(platform_rect.height))

            )
            
            screen.blit(scaled_image, platform_rect)
        
        else:  # Fallback to solid color if no image
            pygame.draw.rect(screen, platform.color, platform_rect)

    for player in active_players:

        player_rect = camera.apply(player)
        scaled_rect = pygame.Rect(
            player_rect.x,
            player_rect.y,
            int(player_rect.width),
            int(player_rect.height)
        )
        pygame.draw.rect(screen, player.color, scaled_rect)

def update_tutorial_controls(active_players, introduce_jumping, introduce_sliding, introduced_controls_state):
    """Allow players to use new controls when reaching new section and tell display_controls function to display new controls"""

    for player in active_players:
        
        if player.on_platform == introduce_jumping and not introduced_controls_state["introduced_jumping"]:
            introduced_controls_state["introduced_jumping"] = True

        elif player.on_platform == introduce_sliding and not introduced_controls_state["introduced_sliding"]:
            introduced_controls_state["introduced_sliding"] = True

    if introduced_controls_state["introduced_jumping"]:
        for player in active_players:
            player.can_jump = True

    if introduced_controls_state["introduced_sliding"]:
        for player in active_players:
            player.can_slide = True


async def main():

    keys_data = await load_json_file('Players/player_controls.json')
    
    level_name = 'tutorial_level'  # Select either tutorial_level or demo_level

    levels_data = await load_json_file(f'Levels/{level_name}.json')

    player1_controls = keys_data['controls']['players']['player1']
    player2_controls = keys_data['controls']['players']['player2']
    player3_controls = keys_data['controls']['players']['player3']
    player4_controls = keys_data['controls']['players']['player4']

    print_player_controls = keys_data['show_controls']['players']

    p1_controls = print_player_controls['player1']
    p3_controls = print_player_controls['player3']
    p4_controls = print_player_controls['player4']

    level_type = levels_data[level_name]['level_type']
    platforms = load_platforms(levels_data, level_name)
    num_of_players = 1

    OG_spawn_point, introduce_jumping, introduce_sliding, death_platforms, next_checkpoints, finish_line = get_special_platforms(platforms, level_name)

    players = {
    "player1": Player(player_id=1, position=OG_spawn_point, controls=player1_controls, color=("#9EBA01")),
    "player2": Player(player_id=2, position=OG_spawn_point, controls=player2_controls, color=("#2276c9")),
    "player3": Player(player_id=3, position=OG_spawn_point, controls=player3_controls, color=("#c7b61a")),
    "player4": Player(player_id=4, position=OG_spawn_point, controls=player4_controls, color=("#c7281a"))
    }

    active_players = []
    
    for number in range(num_of_players):
        active_players.append(players[f'player{number + 1}'])
    
    spawn_point = OG_spawn_point
    checkpoint_increment = 0
    reset_positions = []

    print_player1_controls, print_player2_controls, print_player3_controls, print_player4_controls, p2_active, p3_active, p4_active = determine_blitted_controls(active_players, p1_controls, p3_controls, p4_controls)

    for player in active_players:
        reset_positions.append(spawn_point)
    
    if level_type == 'scrolling':
        next_checkpoint = next_checkpoints[checkpoint_increment]
        level_width, level_height = levels_data[level_name]['camera_width'], levels_data[level_name]['camera_height']
        camera = Camera(width=level_width, height=level_height, window_size=window_size)
        camera.is_active = True # CHANGE LATER
        introduced_controls_state = {"introduced_jumping": False, "introduced_sliding": False}
        
        for player in active_players:
            player.can_jump, player.can_slide = False, False

    else:
        level_width, level_height = 1000, 700
        camera = Camera(width=level_width, height=level_height, window_size=window_size)
        camera.is_active = False
        introduced_controls_state = {"introduced_jumping": True, "introduced_sliding": True}

    running = True
    fixed_delta_time = 1 / 60
    accumulator = 0
    start_timer = pygame.time.get_ticks()
    paused = False
    game_finished = False
    best_player_num = None
    text_color = ("#71d6f5")



    while running:
        dt = clock.tick(60) / 1000.0
        accumulator += dt
        keys = pygame.key.get_pressed()

        if level_name == 'tutorial_level':
            update_tutorial_controls(active_players, introduce_jumping, introduce_sliding, introduced_controls_state)

        for player in active_players:

            if player.position.y > level_height + 100:
                player.reload(spawn_point)

            if player.on_platform == finish_line:
                reset_positions = []
                best_player_num = player.id
                game_finished = True
                text_color = player.color
                checkpoint_increment = 0
                spawn_point = OG_spawn_point

                for player in active_players:
                    reset_positions.append(spawn_point)

                for platform in next_checkpoints:
                    platform.color = "#9ff084"
                
                if level_type == 'scrolling':
                    spawn_point = OG_spawn_point
                    reset_positions = []
                    next_checkpoint = next_checkpoints[checkpoint_increment]
                    introduced_controls_state = {"introduced_jumping": False, "introduced_sliding": False}
                    
                    for player in active_players:
                        reset_positions.append(spawn_point)
                        player.can_jump, player.can_slide = False, False    

            if level_type == 'scrolling':

                if player.on_platform in death_platforms:
                    player.reload(spawn_point)

                if player.on_platform == next_checkpoint:
                    spawn_point = (next_checkpoint.position.x + (next_checkpoint.dimensions[0] / 2), next_checkpoint.start_position.y - next_checkpoint.dimensions[1])
                    next_checkpoint.color = "#228700"
                    reset_positions = []
                    
                    for player in active_players:

                        reset_positions.append(spawn_point)
                    
                    if checkpoint_increment < len(next_checkpoints) - 1:
                        checkpoint_increment += 1
                        next_checkpoint = next_checkpoints[checkpoint_increment]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_r:
                    reload_map(active_players, platforms, reset_positions)  
                    best_player_num = None
                    game_finished = False
                    text_color = ("#71d6f5")

                    if level_name == 'tutorial_level' and spawn_point == OG_spawn_point or next_checkpoints == []:
                        start_timer = pygame.time.get_ticks()
                
                if event.key == pygame.K_p:
                    paused = True
                
                elif paused or game_finished:

                    if event.key == pygame.K_u:
                        paused = False
                    
                    elif event.key == pygame.K_r:
                        reload_map(active_players, platforms, reset_positions)
                        paused = False
                        game_finished = False
                        best_player_num = None
                        text_color = ("#71d6f5")
                        
                        if level_name == 'tutorial_level' and spawn_point == OG_spawn_point or level_name == 'demo_level':
                            start_timer = pygame.time.get_ticks()

        if paused or game_finished:

            freeze_game(screen, clock, window_size, counting_string, paused, game_finished, best_player_num, text_color)

        if not paused and not game_finished:

            while accumulator >= fixed_delta_time:
                update_game_logic(fixed_delta_time, active_players, platforms, keys, position=spawn_point)
                accumulator -= fixed_delta_time
                camera.update(active_players, player)

            screen.fill((0, 0, 0))
            
            counting_string = update_timer(start_timer)
            render_game_objects(platforms, active_players, camera)
            display_controls(introduced_controls_state, counting_string, print_player1_controls, print_player2_controls, print_player3_controls, print_player4_controls, p2_active, p3_active, p4_active, timer_color=("#32854b"))

            pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()

# Run the main function
asyncio.run(main())

"""if you read this you are nice"""