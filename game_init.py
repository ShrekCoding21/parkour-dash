import pygame
import asyncio
import json
import time
import cv2
from PIL import Image, ImageFilter
from Players.player import Player
from Platforms.platform import Platform
from camera import Camera
from Buttons.buttons import Button

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

async def load_level(level_name, num_of_players):

    keys_data = await load_json_file('Players/player_controls.json')
    
    # Select tutorial_level, demo_level, or home

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

    OG_spawn_point, introduce_jumping, introduce_sliding, introduce_jumpsliding, death_platforms, show_settings, next_checkpoints, finish_line = get_special_platforms(platforms, level_name)

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

    introduced_controls_state = {"introduced_jumping": False, "introduced_sliding": False}

    if level_type == 'scrolling':
        
        level_width, level_height = levels_data[level_name]['camera_dimensions'][0], levels_data[level_name]['camera_dimensions'][1]
        camera = Camera(width=level_width, height=level_height, window_size=window_size)
        camera.is_active = True
        
        if level_name == 'tutorial_level':

            next_checkpoint = next_checkpoints[checkpoint_increment]

            for player in active_players:
                player.can_jump, player.can_slide = False, False

    else:
        level_width, level_height = 1000, 700
        camera = Camera(width=level_width, height=level_height, window_size=window_size)
        camera.is_active = False
        introduced_controls_state["introduced_jumping"], introduced_controls_state['introduced_sliding'] = True, True
        next_checkpoint = None
        checkpoint_increment = None

    return show_settings, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, introduce_jumping, introduce_sliding, OG_spawn_point, introduce_jumpsliding, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player2_controls, print_player3_controls, print_player4_controls, p2_active, p3_active, p4_active, next_checkpoint

async def load_cutscene(video_path, time_video_started, scale_to=None):
    
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40)
    video = cv2.VideoCapture(video_path)
    print_skip1 = font.render("Press space", True, ("#ffffff"))
    print_skip2 = font.render("or s to skip", True, ("#ffffff"))
    print_skip1_rect = print_skip1.get_rect(topleft=(10, 20))
    print_skip2_rect = print_skip2.get_rect(topleft=(10, 60))
    time_until_skip = 8

    success, video_image = video.read()
    if not success:
        print(f"Failed to load video: {video_path}")
        return

    fps = video.get(cv2.CAP_PROP_FPS)
    frame_delay = 1 / fps

    original_width, original_height = video_image.shape[1::-1]
    target_width, target_height = scale_to if scale_to else (original_width, original_height)

    window = pygame.display.set_mode((target_width, target_height))

    run = success
    while run:
        
        video_time = time.time() - time_video_started

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            
            elif video_time >= time_until_skip and event.type == pygame.KEYDOWN:  # Skip cutscene

                if event.key == pygame.K_s or event.key == pygame.K_SPACE:

                    run = False
                    break

        if not run:
            break

        success, video_image = video.read()

        if success:
            resized_image = cv2.resize(video_image, (target_width, target_height))

            video_surf = pygame.image.frombuffer(
                resized_image.tobytes(), resized_image.shape[1::-1], "BGR")
        else:
            run = False
            break

        window.blit(video_surf, (0, 0))

        if video_time >= time_until_skip:
            window.blit(print_skip1, print_skip1_rect)
            window.blit(print_skip2, print_skip2_rect)

        pygame.display.flip()

        await asyncio.sleep(frame_delay)

    window.fill((0, 0, 0))
    pygame.display.flip()



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

async def settings_menu(screen, window_size, time_entered_settings):

    blur_duration = 0.85
    max_blur_radius = 10
    screen_surface = pygame.image.tobytes(screen, "RGBA")
    pil_image = Image.frombytes("RGBA", screen.get_size(), screen_surface)

    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 55)
    lil_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 35)
    button_image = pygame.image.load("Buttons/tutorial_button.png").convert_alpha()
    small_button = pygame.image.load("Buttons/lilbutton.png").convert_alpha()

    EXIT_SETTINGS = Button(image=button_image, pos=(500, 500), text_input="exit", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
    ONE_PLAYER = Button(image=small_button, pos=(470, 250), text_input="1p", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 25), base_color="#167fc9", hovering_color="#F59071")
    TWO_PLAYER = Button(image=small_button, pos=(550, 250), text_input="2p", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 25), base_color="#167fc9", hovering_color="#F59071")
    THREE_PLAYER = Button(image=small_button, pos=(630, 250), text_input="3p", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 25), base_color="#167fc9", hovering_color="#F59071")
    FOUR_PLAYER = Button(image=small_button, pos=(710, 250), text_input="4p", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 25), base_color="#167fc9", hovering_color="#F59071")

    buttons = [EXIT_SETTINGS, ONE_PLAYER, TWO_PLAYER, THREE_PLAYER, FOUR_PLAYER]

    while True:

        MENU_MOUSE_POS = pygame.mouse.get_pos()
        settings_time_elapsed = time.time() - time_entered_settings

        if settings_time_elapsed < blur_duration:
            blur_radius = (settings_time_elapsed / blur_duration) * max_blur_radius
        else:
            blur_radius = max_blur_radius

        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                
                if EXIT_SETTINGS.checkForInput(MENU_MOUSE_POS):
                    print("exit")
                    return False
                
                elif ONE_PLAYER.checkForInput(MENU_MOUSE_POS):
                    print("one p")
                    return "one player"
                
                elif TWO_PLAYER.checkForInput(MENU_MOUSE_POS):
                    print("2p")
                    return "two players"

                elif THREE_PLAYER.checkForInput(MENU_MOUSE_POS):
                    print("3p")
                    return "three players"
                
                elif FOUR_PLAYER.checkForInput(MENU_MOUSE_POS):
                    print("4p")
                    return "four players"
        
        blurred_image = pil_image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        blurred_surface = pygame.image.frombytes(blurred_image.tobytes(), screen.get_size(), "RGBA")
        screen.blit(blurred_surface, (0, 0))

        if settings_time_elapsed >= blur_duration:
            printsettings = font.render("settings", True, ("#71d6f5"))
            print_player_num = lil_font.render("# of players:", True, ("#71d6f5"))
            text_rect1 = printsettings.get_rect(center=(window_size[0] // 2, window_size[1] // 2 - 200))
            text_rect2 = print_player_num.get_rect(center=(260, 250))
            screen.blit(printsettings, text_rect1)
            screen.blit(print_player_num, text_rect2)
            
            for button in buttons:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)

        pygame.display.flip()
        await asyncio.sleep(0)

async def pause_menu(screen, window_size, time_paused):

    blur_duration = 0.85
    max_blur_radius = 10
    screen_surface = pygame.image.tobytes(screen, "RGBA")
    pil_image = Image.frombytes("RGBA", screen.get_size(), screen_surface)

    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 55)
    button_image = pygame.image.load("Buttons/tutorial_button.png").convert_alpha()

    printtext = font.render("Paused", True, ("#71d6f5"))
    text_rect = printtext.get_rect(center=(window_size[0] // 2, window_size[1] // 2 - 200))

    RESUME_BUTTON = Button(image=button_image, pos=(500, 260), text_input="resume", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
    RESTART_LEVEL = Button(image=button_image, pos=(500, 330), text_input="restart", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 35), base_color="#167fc9", hovering_color="#F59071")
    DISPLAY_CONTROLS = Button(image=button_image, pos=(500, 400), text_input="controls", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 30), base_color="#167fc9", hovering_color="#F59071")
    SETTINGS = Button(image=button_image, pos=(500, 470), text_input="settings", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 30), base_color="#167fc9", hovering_color="#F59071")
    MAIN_MENU = Button(image=button_image, pos=(500, 540), text_input="home", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color="#167fc9", hovering_color="#F59071")

    buttons = [RESUME_BUTTON, RESTART_LEVEL, DISPLAY_CONTROLS, SETTINGS, MAIN_MENU]

    while True:
        
        MENU_MOUSE_POS = pygame.mouse.get_pos()
        paused_time_elapsed = time.time() - time_paused

        if paused_time_elapsed < blur_duration:
            blur_radius = (paused_time_elapsed / blur_duration) * max_blur_radius
        else:
            blur_radius = max_blur_radius
        
        blurred_image = pil_image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        blurred_surface = pygame.image.frombytes(blurred_image.tobytes(), screen.get_size(), "RGBA")
        
        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                
                if RESUME_BUTTON.checkForInput(MENU_MOUSE_POS):
                    return False
                
                elif RESTART_LEVEL.checkForInput(MENU_MOUSE_POS):
                    return "level restart"
                
                elif DISPLAY_CONTROLS.checkForInput(MENU_MOUSE_POS):
                    print("display controls")

                elif SETTINGS.checkForInput(MENU_MOUSE_POS):
                    return "go to settings"
                
                elif MAIN_MENU.checkForInput(MENU_MOUSE_POS):
                    return "go to home"

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

        screen.blit(blurred_surface, (0, 0))
        
        if paused_time_elapsed >= blur_duration:
            printtext = font.render("Paused", True, ("#71d6f5"))
            text_rect = printtext.get_rect(center=(window_size[0] // 2, window_size[1] // 2 - 200))
            screen.blit(printtext, text_rect)
            
            for button in buttons:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)

        pygame.display.flip()
        await asyncio.sleep(0)


def level_complete(screen, clock, window_size, counting_string, best_player_num, text_color):

    text1 = f'player {best_player_num} wins!'
    text2 = 'press (r) to restart game'
    text3 = f'completion time: {counting_string}'

    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 35)
    texts = [text1, text2, text3]

    offset = 30
    for text in texts:
        printtext = font.render(text, True, (text_color))
        text_rect = printtext.get_rect(center=(window_size[0] // 2, window_size[1] // 2 - offset))
        screen.blit(printtext, text_rect)
        offset -= 60

    pygame.display.flip()
    clock.tick(10)

def introduce_controls(blit_jumpslide):

    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 30)

    print_jumpslide_tutorial1 = font.render("press jump and slide keys", True, ("#00f7f7"))
    print_jumpslide_tutorial2 = font.render("together to leap", True, ("#00f7f7"))
    jumpslide_tutorial_rect1 = print_jumpslide_tutorial1.get_rect(center=(500, 180))
    jumpslide_tutorial_rect2 = print_jumpslide_tutorial2.get_rect(center=(500, 220))
    
    if blit_jumpslide:
        screen.blit(print_jumpslide_tutorial1, jumpslide_tutorial_rect1)
        screen.blit(print_jumpslide_tutorial2, jumpslide_tutorial_rect2)

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
        'esc: game unpause',
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

        elif platform.name == f"checkpoint{checkpoint_num}":
            next_checkpoints.append(platform)
            checkpoint_num += 1

        elif platform.name == "finish-line":
            finish_line = platform

        if level_name == "tutorial_level":
            
            if platform.name == "introduce-jumping":
                intro_to_jumping = platform

            elif platform.name == "introduce-sliding":
                intro_to_sliding = platform

            elif platform.name == "introduce-jumpsliding":
                intro_to_jumpslide = platform

            elif platform.name == f"death-form{deathpoint_num}":
                deathforms.append(platform)
                deathpoint_num += 1

            show_settings = None

        elif level_name == "home":

            if platform.name == "settings":
                show_settings = platform
                intro_to_jumping, intro_to_sliding, intro_to_jumpslide, next_checkpoints = None, None, None, None

        
        
        else:
            intro_to_jumping, intro_to_sliding, intro_to_jumpslide, next_checkpoints, show_settings = None, None, None, None, None

    return spawn_point, intro_to_jumping, intro_to_sliding, intro_to_jumpslide, deathforms, show_settings, next_checkpoints, finish_line

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