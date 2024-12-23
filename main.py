import pygame
import asyncio
import json
import time
import sys
import pyodide # ignore what IDE says; THIS IS NECESSARY FOR CODE TO RUN IN BROWSER
import pygbag
from PIL import Image, ImageFilter
from sprites import Spritesheet
from Players.player import Player
from camera import Camera
from Buttons.buttons import Button
from game_init import load_platforms, level_complete, introduce_controls, reload_map, display_controls, determine_blitted_controls, update_game_logic, update_timer, get_special_platforms, render_game_objects, update_tutorial_controls

# Change this to whatever weather you want to test or leave as None to use API data
TEST_WEATHER = None

WEB_ENVIRONMENT = False
try:
    import pygbag.fs # type: ignore
    WEB_ENVIRONMENT = True
except ImportError:
    pass  # We're not running in a web environment

pygame.init()
window_size = (1000, 700)
canvas = pygame.Surface(window_size)
screen = pygame.display.set_mode(window_size)
clock = pygame.time.Clock()

pygame.display.set_caption("Parkour Dash")

if sys.platform == "emscripten":    
    platform.document.body.style.background = "#050a36"

screen.fill("#020626")
loading_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40)
loading_text = loading_font.render("Loading...", True, ("#71d6f5"))
loading_rect = loading_text.get_rect(center=(window_size[0] // 2, window_size[1] // 2))
screen.blit(loading_text, loading_rect)
pygame.display.update()

async def game_init():
    if not TEST_WEATHER:
        try:
            weather_data = await read_weather_file()
            if weather_data is None:
                print("No weather data found. Using default values.")
                weather_data = {"weather_code": 0, "temperature": 70, "windspeed": 0}  # Defaults
            return weather_data
        except Exception as e:
            return {"weather_code": 0, "temperature": 70, "windspeed": 0}  # Fallback
    else:
        print(f"Using test weather data: {TEST_WEATHER}")
        return TEST_WEATHER

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

async def read_weather_file():
    if not TEST_WEATHER:
        try:
            
            from js import eval as eval_js
            # JavaScript code to fetch data from localStorage
            js_code = """
                (function() {
                    try {
                        const data = localStorage.getItem("weather_data");
                        if (data) {
                            console.log("Weather data found in localStorage:", data);
                            console.log("returning data to python");
                            return data; // Return as string
                        } else {
                            console.log("No weather data found in localStorage.");
                            return null;
                        }
                    } catch (error) {
                        console.error("Error accessing localStorage:", error);
                        return null;
                    }
                })()
            """
            
            # Execute JavaScript code using eval_js
            weather_data = eval_js(js_code)
            
            if weather_data:
                # Parse JSON string into a Python dictionary
                try:
                    weather_data = json.loads(weather_data)
                    print(f"weather data: {weather_data}")
                    return weather_data
                except json.JSONDecodeError:
                    print("Error decoding weather data. Using default values.")
        except ImportError as e:
            print(f"Error importing JavaScript module: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON data: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error retrieving weather data: {e}")
            return None
            
        except Exception as e:
            print(f"Error retrieving weather data: {e}")
            return None



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

async def load_cutscene(canvas):

    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40)
    cutscene = Spritesheet('assets/parkour_dash_intro_sprite.png', 1000, 700)
    cutscene_frames, cutscene_total_frames, animation_speed = cutscene.get_all_frames('cutscene.png')
    index = 0
    animation_start_time = pygame.time.get_ticks()
    last_update_time = pygame.time.get_ticks()
    running = True
    show_skip1 = font.render("Press space or", True, ("#ffffff"))
    show_skip2 = font.render("s to skip", True, ("#ffffff"))
    show_skip1_rect = show_skip1.get_rect(topleft=(10, 10))
    show_skip2_rect = show_skip2.get_rect(topleft=(10, 50))
    time_to_skip = 8000 # CHANGE THIS LATER; should be 8000 normally

    while running:
        current_time = pygame.time.get_ticks()
        time_playing = current_time - animation_start_time

        if current_time - last_update_time > animation_speed:
            index = (index + 1) % cutscene_total_frames
            last_update_time = current_time

            if index == 289:
                running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif time_playing >= time_to_skip and event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_s or event.key == pygame.K_SPACE:
                    running = False

        canvas.fill((0, 0, 0))
        
        current_frame = cutscene_frames[index]
        
        frame_rect = current_frame.get_rect(center=(canvas.get_width() // 2, canvas.get_height() // 2))
        canvas.blit(current_frame, frame_rect.topleft)

        screen.blit(canvas, (0, 0))

        if time_playing >= time_to_skip:

            screen.blit(show_skip1, show_skip1_rect)
            screen.blit(show_skip2, show_skip2_rect)

        pygame.display.update()
        await asyncio.sleep(0)

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
                    return False
                
                elif ONE_PLAYER.checkForInput(MENU_MOUSE_POS):
                    return "one player"
                
                elif TWO_PLAYER.checkForInput(MENU_MOUSE_POS):
                    return "two players"

                elif THREE_PLAYER.checkForInput(MENU_MOUSE_POS):
                    return "three players"
                
                elif FOUR_PLAYER.checkForInput(MENU_MOUSE_POS):
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
                    pass

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



"""parkour_dash.py code goes here"""



async def main():

    current_weather = await game_init()
    weather_codes = await load_json_file('weather_codes.json')

    for condition in weather_codes['weather-codes'].keys():

        if current_weather['weather_code'] in weather_codes['weather-codes'][condition]:

            print(condition)
            weather_condition = condition
            print(f"weather_condition = {weather_condition}")

    await load_cutscene(canvas)

    level_name = 'home'
    bg_image = pygame.image.load("assets/parkour_dash_background.png").convert_alpha()
    bg_image = pygame.transform.scale(bg_image, window_size)
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 60)
    lil_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 25)
    text_color = ("#71d6f5")

    num_of_players = 1
    show_settings, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, introduce_jumping, introduce_sliding, OG_spawn_point, introduce_jumpsliding, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player2_controls, print_player3_controls, print_player4_controls, p2_active, p3_active, p4_active, next_checkpoint = await load_level(level_name, num_of_players)   
    print(f"current weather (in main): {current_weather}")

    print_welcome1 = font.render("welcome to", True, (text_color))
    print_welcome2 = font.render("project AstRA", True, (text_color))
    show_tutorial_level1 = lil_font.render("jump here for tutorial", True, (text_color))
    show_tutorial_level2 = lil_font.render("↓", True, (text_color))
    show_settings1 = lil_font.render("← settings", True, (text_color))
    highlight_game_controls1 = lil_font.render("these could be useful→", True, (text_color))
    yay_weather = font.render("yay weather", True, (text_color))
    print_weather_condition = font.render(f"{weather_condition}", True, (text_color))

    print_welcome1_rect = print_welcome1.get_rect(center=(500, 155))
    print_welcome2_rect = print_welcome2.get_rect(center=(500, 230))
    show_tutorial_level1_rect = show_tutorial_level1.get_rect(center=(600, 525))
    show_tutorial_level2_rect = show_tutorial_level2.get_rect(center=(550, 550))
    show_settings1_rect = show_settings1.get_rect(center=(125, 475))
    highlight_game_controls1_rect = highlight_game_controls1.get_rect(center=(435, 50))
    yay_weather_rect = yay_weather.get_rect(center=(500, 350))
    weather_condition_rect = print_weather_condition.get_rect(center=(500, 400))

    running = True
    fixed_delta_time = 1 / 60
    accumulator = 0
    start_timer = pygame.time.get_ticks()
    paused = False
    editing_settings = False
    reload_players = False
    game_finished = False
    best_player_num = None
    platforms_used = []
    RELOAD = Button(image=pygame.image.load("Buttons/reload_button.png").convert_alpha(), pos=(85, 43), text_input=None, font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
    PAUSE = Button(image=pygame.image.load("Buttons/pause_button.png").convert_alpha(), pos=(30, 35), text_input=None, font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color=("White"), hovering_color=("White"))



    while running:
        dt = clock.tick(60) / 1000.0
        accumulator += dt
        keys = pygame.key.get_pressed()
        MENU_MOUSE_POS = pygame.mouse.get_pos()

        if level_name == 'tutorial_level':
            update_tutorial_controls(active_players, introduce_jumping, introduce_sliding, introduced_controls_state)

        for player in active_players:

            if player.id == 1:

                # print(editing_settings)

                # print(player.position)

                if player.on_platform:
                    current_platform = player.on_platform.name
                    # print(current_platform)

                    if current_platform not in platforms_used:
                        platforms_used.append(current_platform)
                
            if player.on_platform == introduce_jumpsliding and level_name == 'tutorial_level':
                blit_jumpslide = True
            else:
                blit_jumpslide = False

            if player.position.y > level_height + 100:

                if level_name == 'home':
                    level_name = 'tutorial_level' # change this to level currently being developed for testing; if you fall in pit in home screen, you teleport to that level; make sure this is json file name as well
                    show_settings, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, introduce_jumping, introduce_sliding, OG_spawn_point, introduce_jumpsliding, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player2_controls, print_player3_controls, print_player4_controls, p2_active, p3_active, p4_active, next_checkpoint = await load_level(level_name, num_of_players)
                    start_timer = pygame.time.get_ticks()

                else:

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
                
                if level_name == 'tutorial_level':
                    next_checkpoint = next_checkpoints[checkpoint_increment]
                    introduced_controls_state["introduced_jumping"], introduced_controls_state['introduced_sliding'] = False, False
                    
                    for platform in next_checkpoints:
                        platform.color = "#9ff084"

                    for player in active_players:
                        player.can_jump, player.can_slide = False, False    

            if level_name == 'tutorial_level':

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
            
            elif level_name == 'home':

                if player.on_platform == show_settings and not editing_settings:

                    if not reload_players:

                        time_entered_settings = time.time()
                        editing_settings = True
                    
                    else:

                        player.reload(spawn_point)
                        start_timer = pygame.time.get_ticks()
                        reload_players = False

        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                print(platforms_used)
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:

                if RELOAD.checkForInput(MENU_MOUSE_POS):
                    reload_map(active_players, platforms, reset_positions)
                    best_player_num = None
                    game_finished = False
                    text_color = ("#71d6f5")

                    if level_name == 'tutorial_level' and spawn_point == OG_spawn_point or next_checkpoints == []:
                        start_timer = pygame.time.get_ticks()

                if PAUSE.checkForInput(MENU_MOUSE_POS):
                    time_paused = time.time()
                    paused = True
            
            elif event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_r:
                    reload_map(active_players, platforms, reset_positions)  
                    best_player_num = None
                    game_finished = False
                    text_color = ("#71d6f5")

                    if level_name == 'tutorial_level' and spawn_point == OG_spawn_point or next_checkpoints == []:
                        start_timer = pygame.time.get_ticks()
                
                if event.key == pygame.K_p:
                    time_paused = time.time()
                    paused = True
                
                elif paused or game_finished:

                    if event.key == pygame.K_u or not pause_menu(screen, window_size, time_paused):
                        paused = False
                    
                    elif event.key == pygame.K_r:
                        reload_map(active_players, platforms, reset_positions)
                        paused = False
                        game_finished = False
                        best_player_num = None
                        text_color = ("#71d6f5")
                        
                        if level_name == 'tutorial_level' and spawn_point == OG_spawn_point or level_name == 'demo_level':
                            start_timer = pygame.time.get_ticks()

        if paused:
            
            action = await pause_menu(screen, window_size, time_paused)

            if action == False:
                paused = False
            
            elif action == "level restart":

                reset_positions = []
                checkpoint_increment = 0
                spawn_point = OG_spawn_point

                for player in active_players:
                    reset_positions.append(spawn_point)

                if level_name != 'home':
                    for platform in next_checkpoints:
                        platform.color = "#9ff084"
                
                if level_name == 'tutorial_level':
                    next_checkpoint = next_checkpoints[checkpoint_increment]
                    introduced_controls_state["introduced_jumping"], introduced_controls_state['introduced_sliding'] = False, False
                    
                    for player in active_players:
                        player.can_jump, player.can_slide = False, False

                reload_map(active_players, platforms, reset_positions)
                start_timer = pygame.time.get_ticks()
                paused = False

            elif action == "go to home":

                level_name = 'home'
                show_settings, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, introduce_jumping, introduce_sliding, OG_spawn_point, introduce_jumpsliding, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player2_controls, print_player3_controls, print_player4_controls, p2_active, p3_active, p4_active, next_checkpoint = await load_level(level_name, num_of_players)
                paused = False
                start_timer = pygame.time.get_ticks()

            elif action == "go to settings" and not editing_settings:

                time_entered_settings = time.time()
                print("show settings (via pause menu)")
                paused = False
                editing_settings = True

        elif editing_settings:

            settings_action = await settings_menu(screen, window_size, time_entered_settings)

            if not settings_action:
                reload_players = True
                editing_settings = False

            elif settings_action == "one player":
                
                if len(active_players) != 1:
                    num_of_players = 1
                    show_settings, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, introduce_jumping, introduce_sliding, OG_spawn_point, introduce_jumpsliding, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player2_controls, print_player3_controls, print_player4_controls, p2_active, p3_active, p4_active, next_checkpoint = await load_level(level_name, num_of_players)
                    reload_players = True
                    
                editing_settings = False
            
            elif settings_action == "two players":

                if len(active_players) != 2:
                    num_of_players = 2
                    show_settings, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, introduce_jumping, introduce_sliding, OG_spawn_point, introduce_jumpsliding, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player2_controls, print_player3_controls, print_player4_controls, p2_active, p3_active, p4_active, next_checkpoint = await load_level(level_name, num_of_players)
                    reload_players = True

                editing_settings = False
            
            elif settings_action == "three players":

                if len(active_players) != 3:
                    num_of_players = 3
                    show_settings, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, introduce_jumping, introduce_sliding, OG_spawn_point, introduce_jumpsliding, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player2_controls, print_player3_controls, print_player4_controls, p2_active, p3_active, p4_active, next_checkpoint = await load_level(level_name, num_of_players)
                    reload_players = True

                editing_settings = False
            
            elif settings_action == "four players":

                if len(active_players) != 4:
                    num_of_players = 4
                    show_settings, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, introduce_jumping, introduce_sliding, OG_spawn_point, introduce_jumpsliding, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player2_controls, print_player3_controls, print_player4_controls, p2_active, p3_active, p4_active, next_checkpoint = await load_level(level_name, num_of_players)
                    reload_players = True

                editing_settings = False

            
        elif game_finished:

            level_complete(screen, clock, window_size, counting_string, best_player_num, text_color)

        else:

            while accumulator >= fixed_delta_time:
                update_game_logic(fixed_delta_time, active_players, platforms, keys, position=spawn_point)
                accumulator -= fixed_delta_time
                camera.update(active_players, player)

            screen.fill((0, 0, 0))
            
            counting_string = update_timer(start_timer)
            screen.blit(bg_image, (0, 0))
            render_game_objects(platforms, active_players, camera)
            display_controls(introduced_controls_state, counting_string, print_player1_controls, print_player2_controls, print_player3_controls, print_player4_controls, p2_active, p3_active, p4_active, timer_color=("#32854b"))
            introduce_controls(blit_jumpslide)

            if level_name == 'home':
                screen.blit(print_welcome1, print_welcome1_rect)
                screen.blit(print_welcome2, print_welcome2_rect)
                screen.blit(show_tutorial_level1, show_tutorial_level1_rect)
                screen.blit(show_tutorial_level2, show_tutorial_level2_rect)
                screen.blit(show_settings1, show_settings1_rect)
                screen.blit(highlight_game_controls1, highlight_game_controls1_rect)

            if current_weather:
                screen.blit(yay_weather, yay_weather_rect)
                screen.blit(print_weather_condition, weather_condition_rect)

                
            for button in [RELOAD, PAUSE]:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)

            pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()

# Run the main function
asyncio.run(main())

"""if you read this you are nice"""