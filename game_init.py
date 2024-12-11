import pygame
import asyncio
import json
import time
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

async def pause_menu(screen, window_size, time_paused):

    blur_duration = 1
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
                    print("go to settings")
                
                elif MAIN_MENU.checkForInput(MENU_MOUSE_POS):
                    print("home")

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u:
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
    print_jumpslide_tutorial2 = font.render("together to jumpslide", True, ("#00f7f7"))
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

            if platform.name == "introduce-jumpsliding":
                intro_to_jumpslide = platform

            if platform.name == f"death-form{deathpoint_num}":
                deathforms.append(platform)
                deathpoint_num += 1
        
        else:
            intro_to_jumping, intro_to_sliding, intro_to_jumpslide = None, None, None

    return spawn_point, intro_to_jumping, intro_to_sliding, intro_to_jumpslide, deathforms, next_checkpoints, finish_line

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