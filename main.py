import os
import sys
import pygame
import asyncio
import json
import time
import pyodide  # Necessary for browser environment
import pygbag
from PIL import Image, ImageFilter

# Dynamically adjust the system path to ensure local imports work
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)  # Add current directory to sys.path
sys.path.append(os.path.join(base_dir, 'Players'))  # Add specific folders if needed
sys.path.append(os.path.join(base_dir, 'Buttons'))  # Add other specific folders if necessary

# Local imports
from flashlight import Flashlight
from Players.player import Player
from camera import Camera
from artifacts import Artifact
from popups import Popup
from Buttons.buttons import Button
from game_init import (
    getArtifacts,
    render_artifacts,
    render_artifact_count,
    load_platforms,
    introduce_controls,
    reload_map,
    display_controls,
    determine_blitted_controls,
    update_game_logic,
    update_timer,
    render_timer,
    get_special_platforms,
    getSplitscreenLayout,
    renderSplitscreenLayout,
    render_game_objects,
    update_tutorial_controls,
)

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

    levels_data = await load_json_file(f'Levels/{level_name}/{level_name}.json')
    bg_image = pygame.image.load(f'Levels/{level_name}/assets/bg_image.png').convert_alpha()
    bg_image = pygame.transform.scale(bg_image, window_size)

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

    OG_spawn_point, death_platforms, next_checkpoints, finish_line = get_special_platforms(platforms, level_name)

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

    print_player1_controls, print_player3_controls, print_player4_controls = determine_blitted_controls(p1_controls, p3_controls, p4_controls)

    for player in active_players:
        reset_positions.append(spawn_point)

    introduced_controls_state = {"introduced_jumping": True, "introduced_sliding": True}
    show_controls = True if level_name in ["Home", "Tutorial_level"] else False

    if level_type == 'scrolling':
        
        level_width, level_height = levels_data[level_name]['camera_dimensions'][0], levels_data[level_name]['camera_dimensions'][1]
        camera = Camera(width=level_width, height=level_height, window_size=window_size, zoom=1.0)
        camera.is_active = True
        next_checkpoint = next_checkpoints[checkpoint_increment]

    else:
        level_width, level_height = 1000, 700
        camera = Camera(width=level_width, height=level_height, window_size=window_size, zoom=1.0)
        camera.is_active = False
        introduced_controls_state["introduced_jumping"], introduced_controls_state['introduced_sliding'] = True, True
        next_checkpoint = None
        checkpoint_increment = None

    return show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint

async def newPlayerCount(new_num_of_players ,active_players, level_name):
    if len(active_players) != new_num_of_players:
        num_of_players = new_num_of_players
        show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
    return active_players

async def settings_menu(screen, window_size, time_entered_settings):

    blur_duration = 0
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
                    return 1
                
                elif TWO_PLAYER.checkForInput(MENU_MOUSE_POS):
                    return 2

                elif THREE_PLAYER.checkForInput(MENU_MOUSE_POS):
                    return 3
                
                elif FOUR_PLAYER.checkForInput(MENU_MOUSE_POS):
                    return 4
        
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

async def pause_menu(screen, level_name, show_controls, window_size, time_paused):

    blur_duration = 0
    max_blur_radius = 10
    screen_surface = pygame.image.tobytes(screen, "RGBA")
    pil_image = Image.frombytes("RGBA", screen.get_size(), screen_surface)

    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 55)
    button_image = pygame.image.load("Buttons/tutorial_button.png").convert_alpha()

    printtext = font.render("Paused", True, ("#71d6f5"))
    text_rect = printtext.get_rect(center=(window_size[0] // 2, window_size[1] // 2 - 200))

    RESUME_BUTTON = Button(image=button_image, pos=(500, 260), text_input="resume", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
    RESTART_LEVEL = Button(image=button_image, pos=(500, 330), text_input="restart", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 35), base_color="#167fc9", hovering_color="#F59071")

    if level_name in ["Home", "Tutorial_level"]:
        
        SETTINGS = Button(image=button_image, pos=(500, 400), text_input="settings", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 30), base_color="#167fc9", hovering_color="#F59071")
        MAIN_MENU = Button(image=button_image, pos=(500, 470), text_input="home", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
        buttons = [RESUME_BUTTON, RESTART_LEVEL, SETTINGS, MAIN_MENU]
    
    else:

        SETTINGS = Button(image=button_image, pos=(500, 470), text_input="settings", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 30), base_color="#167fc9", hovering_color="#F59071")
        MAIN_MENU = Button(image=button_image, pos=(500, 540), text_input="home", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
        DISPLAY_CONTROLS = Button(image=button_image, pos=(500, 400), text_input="controls", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 30), base_color="#167fc9", hovering_color="#F59071")
        HIDE_CONTROLS = Button(image=button_image, pos=(500, 400), text_input="hide controls", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 20), base_color="#167fc9", hovering_color="#F59071")
        buttons = [RESUME_BUTTON, RESTART_LEVEL, HIDE_CONTROLS, SETTINGS, MAIN_MENU] if show_controls else [RESUME_BUTTON, RESTART_LEVEL, DISPLAY_CONTROLS, SETTINGS, MAIN_MENU]

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

                elif SETTINGS.checkForInput(MENU_MOUSE_POS):
                    return "go to settings"
                
                elif MAIN_MENU.checkForInput(MENU_MOUSE_POS):
                    return "go to home"

                if level_name not in ["Home", "Tutorial_level"]:

                    if DISPLAY_CONTROLS.checkForInput(MENU_MOUSE_POS) or HIDE_CONTROLS.checkForInput(MENU_MOUSE_POS):
                        return "show controls"

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

        screen.blit(blurred_surface, (0, 0))
        
        if paused_time_elapsed >= blur_duration:
            screen.blit(printtext, text_rect)
            
            for button in buttons:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)

        pygame.display.flip()
        await asyncio.sleep(0)

async def level_completed(screen, level_name, text_color, window_size, popup_text, time_finished):
    
    blur_duration = 0
    max_blur_radius = 10
    screen_surface = pygame.image.tobytes(screen, "RGBA")
    pil_image = Image.frombytes("RGBA", screen.get_size(), screen_surface)

    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 55)
    button_image = pygame.image.load("Buttons/tutorial_button.png").convert_alpha()

    printtext = font.render(f"{level_name} complete!", True, ("#71d6f5"))
    text_rect = printtext.get_rect(center=(window_size[0] // 2, window_size[1] // 2 - 200))
    base_color = "#167fc9"
    hovering_color = "#F59071"

    artifact_information = Popup(name="artifact_info", screen=screen, text=popup_text, theme_color=text_color, button_text="cool", visible=False)
    artifact_information.font_size, artifact_information.max_line_length = 23, 40

    RESTART_LEVEL = Button(image=button_image, pos=(500, 260), text_input="restart", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 35), base_color=base_color, hovering_color=hovering_color)
    ARTIFACT_INFO = Button(image=button_image, pos=(500, 330), text_input="artifact info", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 18), base_color=base_color, hovering_color=hovering_color)
    MAIN_MENU = Button(image=button_image, pos=(500, 400), text_input="home", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color=base_color, hovering_color=hovering_color)
    buttons = [RESTART_LEVEL, ARTIFACT_INFO, MAIN_MENU]

    while True:
        
        MENU_MOUSE_POS = pygame.mouse.get_pos()
        time_elapsed = time.time() - time_finished

        if time_elapsed < blur_duration:
            blur_radius = (time_elapsed / blur_duration) * max_blur_radius
        else:
            blur_radius = max_blur_radius
        
        blurred_image = pil_image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        blurred_surface = pygame.image.frombytes(blurred_image.tobytes(), screen.get_size(), "RGBA")
        
        for event in pygame.event.get():
            
            artifact_information.handle_event(event)

            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                
                if RESTART_LEVEL.checkForInput(MENU_MOUSE_POS) and not artifact_information.visible:
                    return "level restart"
                
                elif ARTIFACT_INFO.checkForInput(MENU_MOUSE_POS) and not artifact_information.visible:
                    artifact_information.visible = True
                
                elif MAIN_MENU.checkForInput(MENU_MOUSE_POS) and not artifact_information.visible:
                    return "go to home"

        screen.blit(blurred_surface, (0, 0))
        
        if time_elapsed >= blur_duration:
            screen.blit(printtext, text_rect)
            
            for button in buttons:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)
                artifact_information.update()

        pygame.display.flip()
        await asyncio.sleep(0)

async def terus1(active_players, weather_condition):

    from level_init import terusPlatformsInit

    level_name = 'Terus1'
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 60)
    lil_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 30)
    text_color = ("#0c4701")
    magnetite_information = await load_json_file(f"Levels/{level_name}/artifact_info.json")
    post_mission_briefing = magnetite_information['magnetite-info']['after-level-info']

    num_of_players = len(active_players)
    show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)   
    print(f"weather condition: {weather_condition}")
    show_slide, show_slide2, show_checkpoint1_reached, show_checkpoint2_reached, brighten_scene, artifacts = terusPlatformsInit(platforms, level_name)

    popup_data = [

        {"name": "introduce_flashlight",
        "screen": screen,
        "text": "press 'f' to use the flashlight. only one player has access to the flashlight",
        "theme_color": text_color,
        "button_text": "ok",
        "visible": True
    },
    
        {"name": "flashlight_broken",
         "screen": screen,
         "text": "it looks like the flashlight is facing external interference! better hurry...",
         "theme_color": text_color,
         "button_text": "got it",
         "visible": False
    }]
    
    popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in popup_data]
    
    for popup in popups:
        
        if popup.name == "pre_mission_briefing":
            popup.max_line_length = 50
            popup.font_size = 20

    print_need_artifacts = font.render("you need more artifacts", True, text_color)
    need_artifacts_rect = print_need_artifacts.get_rect(center=(window_size[0] // 2, window_size[1] // 2))
    print_show_slide = font.render("← slide...", True, text_color)
    print_show_slide2 = font.render("slide... →", True, text_color)
    show_slide_rect = print_show_slide.get_rect(center=(500, 350))
    show_slide2_rect = print_show_slide2.get_rect(center=(500, 350))
    print_checkpoint1 = lil_font.render("checkpoint1 reached", True, text_color)
    show_checkpoint1 = print_checkpoint1.get_rect(center=(500, 350))
    
    running = True
    fixed_delta_time = 1 / 60
    accumulator = 0
    previous_time = pygame.time.get_ticks()
    start_timer = pygame.time.get_ticks()
    paused = False
    editing_settings = False
    level_complete = False
    flashlight_broken = False
    artifacts_collected = 0
    collected_artifacts = []
    RELOAD = Button(image=pygame.image.load("Buttons/reload_button.png").convert_alpha(), pos=(85, 43), text_input=None, font=lil_font, base_color="#167fc9", hovering_color="#F59071")
    PAUSE = Button(image=pygame.image.load("Buttons/pause_button.png").convert_alpha(), pos=(30, 35), text_input=None, font=lil_font, base_color=("White"), hovering_color=("White"))
    flashlight = Flashlight(screen, intensity=100)
    flashlight.enabled = True
    scene_brightened = False

    while running:
        current_time = pygame.time.get_ticks()
        dt = (current_time - previous_time) / 1000.0
        previous_time = current_time
        accumulator += dt
        keys = pygame.key.get_pressed()
        MENU_MOUSE_POS = pygame.mouse.get_pos()

        for popup in popups:
            if popup.visible:
                popup_active = True
                break
            else:
                popup_active = False

        for player in active_players:
            flashlight.flipped = True if player.facing == -1 else False
            blit_show_slide = player.on_platform == show_slide
            blit_show_slide2 = player.on_platform == show_slide2
            blit_checkpoint1_reached = player.on_platform == show_checkpoint1_reached
            
            if player.on_platform == brighten_scene and not scene_brightened:
                flashlight.enabled = False
                scene_brightened = True

            if player.on_platform == show_checkpoint2_reached and not flashlight_broken:

                for popup in popups:
                    if popup.name == "flashlight_broken":
                        popup.visible = True

                flashlight = Flashlight(screen, intensity=45)
                flashlight.enabled = True
                flashlight_broken = True

            if player.position.y > level_height + 100:
                player.reload(spawn_point)

            if player.on_platform == finish_line:
                reset_positions = [spawn_point] * num_of_players
                level_complete = True
                text_color = player.color
                checkpoint_increment = 0
                spawn_point = OG_spawn_point

            elif player.on_platform in death_platforms:
                player.reload(spawn_point)

            if player.on_platform == next_checkpoint:
                spawn_point = (next_checkpoint.position.x + (next_checkpoint.dimensions[0] / 2), next_checkpoint.start_position.y - next_checkpoint.dimensions[1])
                next_checkpoint.color = "#228700"
                reset_positions = [spawn_point] * num_of_players
                
                if checkpoint_increment < len(next_checkpoints) - 1:
                    checkpoint_increment += 1
                    next_checkpoint = next_checkpoints[checkpoint_increment]
            
            for artifact in artifacts:
                if player.rect.colliderect(artifact.rect) and not artifact.collected and artifact not in collected_artifacts:
                    artifact.collect()
                    artifacts_collected += 1
                    collected_artifacts.append(artifact)

        for event in pygame.event.get():
            
            for popup in popups:
                popup.handle_event(event)

            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.MOUSEBUTTONDOWN and not popup_active:
                if RELOAD.checkForInput(MENU_MOUSE_POS):
                    reload_map(active_players, platforms, reset_positions, artifacts)
                    level_complete = False
                    text_color = ("#71d6f5")
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()

                if PAUSE.checkForInput(MENU_MOUSE_POS):
                    time_paused = time.time()
                    paused = True
            
            elif event.type == pygame.KEYDOWN and not popup_active:
                
                if event.key == pygame.K_f:
                    flashlight.on = not flashlight.on

                if event.key == pygame.K_r:
                    reload_map(active_players, platforms, reset_positions, artifacts)  
                    level_complete = False
                    text_color = ("#71d6f5")
                    flashlight.enabled = True
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()
                
                if event.key == pygame.K_p:
                    time_paused = time.time()
                    paused = True

        if paused:
            action = await pause_menu(screen, level_name, show_controls, window_size, time_paused)
            
            if action == False:
                paused = False
            
            elif action == "level restart":
                show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
                popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in popup_data]
                artifacts_collected = 0
                collected_artifacts = []
                start_timer = pygame.time.get_ticks()
                flashlight_broken = False
                flashlight = Flashlight(screen, intensity=100)
                flashlight.enabled = True
                flashlight.on = False
                show_slide, show_slide2, show_checkpoint1_reached, show_checkpoint2_reached, brighten_scene, artifacts = terusPlatformsInit(platforms, level_name)      
                paused = False
            
            elif action == "go to home":
                level_name = 'home'
                start_timer = pygame.time.get_ticks()
                running = False
            
            elif action == "go to settings" and not editing_settings:
                time_entered_settings = time.time()
                paused = False
                editing_settings = True
            
            elif action == "show controls":
                show_controls = not show_controls
                paused = False

        elif editing_settings:
            settings_action = await settings_menu(screen, window_size, time_entered_settings)
            if not settings_action:
                editing_settings = False
            elif isinstance(settings_action, int):
                active_players = await newPlayerCount(settings_action, active_players, level_name)
                num_of_players = len(active_players)
                editing_settings = False

        elif level_complete:
            if artifacts_collected == 3:
                action = await level_completed(screen, level_name, text_color, window_size, post_mission_briefing, time_finished=time.time())

                if action == "level restart":
                    show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
                    popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in popup_data]
                    artifacts_collected = 0
                    collected_artifacts = []
                    start_timer = pygame.time.get_ticks()
                    flashlight_broken = False
                    flashlight = Flashlight(screen, intensity=100)
                    flashlight.enabled = True
                    flashlight.on = False
                    show_slide, show_slide2, show_checkpoint1_reached, show_checkpoint2_reached, brighten_scene, artifacts = terusPlatformsInit(platforms, level_name)      
                    level_complete = False

                elif action == "go to home":
                    running = False
            
            else:
                screen.blit(print_need_artifacts, need_artifacts_rect)

        else:
            while accumulator >= fixed_delta_time:
                update_game_logic(fixed_delta_time, active_players, platforms, keys, spawn_point, popup_active)
                accumulator -= fixed_delta_time
                flashlight.pos = pygame.Vector2(player.rect.center)

            subscreens = getSplitscreenLayout(canvas, active_players)
            canvas.fill((0, 0, 0))
            renderSplitscreenLayout(canvas, active_players, num_of_players, bg_image, platforms, camera, death_platforms, artifacts, collected_artifacts, flashlight, volcanoes=None, subscreens=subscreens)
            counting_string = update_timer(start_timer)
            render_artifact_count(("#56911f"), artifacts_collected)
            render_timer(lil_font, "#32854b", counting_string)

            for popup in popups:
                popup.update()

            if blit_show_slide:
                screen.blit(print_show_slide, show_slide_rect)
            elif blit_show_slide2:
                screen.blit(print_show_slide2, show_slide2_rect)
            elif blit_checkpoint1_reached:
                screen.blit(print_checkpoint1, show_checkpoint1)

            display_controls(len(active_players), show_controls, introduced_controls_state, print_player1_controls, print_player3_controls, print_player4_controls)
                
            for button in [RELOAD, PAUSE]:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)

            pygame.display.flip()

        await asyncio.sleep(0)

async def scopulosus53(active_players):
    
    from volcanoes import Volcano
    from level_init import scopulosusPlatformsInit

    level_name = 'Scopulosus53'
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 60)
    lil_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 30)
    text_color = ("#0c4701")
    num_of_players = len(active_players)
    show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)   
    introduce_volcano, introduce_deathcano, one_way, artifacts = scopulosusPlatformsInit(level_name, platforms)
    carbon_nanotube_info = await load_json_file(f"Levels/{level_name}/artifact_info.json")
    post_mission_briefing = carbon_nanotube_info["carbon-nanotube-info"]["after-level-info"]

    volcano_introduction = [
    
        {"name": "introduce_volcanoes1",
         "screen": screen,
         "text": "This is a volcano.",
         "theme_color": text_color,
         "button_text": "next",
         "visible": False
    },
    
        {"name": "introduce_volcanoes2",
         "screen": screen,
         "text": "They can be dangerous, but can also be used to your advantage.",
         "theme_color": text_color,
         "button_text": "next",
         "visible": False
    },

        {"name": "introduce_volcanoes3",
         "screen": screen,
         "text": "Use the steam to reach higher platforms.",
         "theme_color": text_color,
         "button_text": "i'll try it",
         "visible": False
    }
    
    ]

    level_tips = [

        {
            "name": "volcano_tip1",
            "screen": screen,
            "text": "These volcanoes seem to be a lot stronger than the previous ones...",
            "theme_color": text_color,
            "button_text": "ok",
            "visible": False
        },

        {
            "name": "one_way_home",
            "screen": screen,
            "text": "looks like theres only one way to go now →",
            "theme_color": text_color,
            "button_text": "bet",
            "visible": False
        }
    ]

    volcano_data = [
        {
            "name": "tutorial_volcano",
            "position": (550, 2900),
            "stretch_size": (1400, 500),
            "steam_height": 800,
            "steam_correction": 30
        },

        {
            "name": "explosion_volcano",
            "position": (1400, 2400),
            "stretch_size": (1400, 1000),
            "steam_height": 1300,
            "steam_correction": 30
        },

        {
            "name": "lil_cano",
            "position": (2700, 1850),
            "stretch_size": (1000, 500),
            "steam_height": 800,
            "steam_correction": 20
        },

        {
            "name": "obstacano1",
            "position": (4000, 2426),
            "stretch_size": (2000, 1000),
            "steam_height": 3000,
            "steam_correction": 30
        },

        {
            "name": "obstacano2",
            "position": (4500, 2426),
            "stretch_size": (2000, 1000),
            "steam_height": 3000,
            "steam_correction": 30
        },

        {
            "name": "obstacano3",
            "position": (5280, 2426),
            "stretch_size": (2000, 1000),
            "steam_height": 3000,
            "steam_correction": 30
        },

        {
            "name": "obstacano4",
            "position": (5800, 2426),
            "stretch_size": (2000, 1000),
            "steam_height": 3000,
            "steam_correction": 30
        },

        {
            "name": "gapcano1",
            "position": (6190, 2426),
            "stretch_size": (2000, 1000),
            "steam_height": 3000,
            "steam_correction": 30  
        },

        {
            "name": "obstacano6",
            "position": (6490, 2426),
            "stretch_size": (2000, 1000),
            "steam_height": 3000,
            "steam_correction": 30
        }
    ]
    
    popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in volcano_introduction + level_tips]
    volcanoes = [Volcano(data["name"], data["position"], data["steam_height"], data["steam_correction"], screen, data["stretch_size"]) for data in volcano_data]
    print_need_artifacts = font.render("you need more artifacts", True, text_color)
    need_artifacts_rect = print_need_artifacts.get_rect(center=(window_size[0] // 2, window_size[1] // 2))

    running = True
    fixed_delta_time = 1 / 60
    accumulator = 0
    previous_time = pygame.time.get_ticks()
    start_timer = pygame.time.get_ticks()
    paused = False
    editing_settings = False
    volcano_introduction_sequence, volcano_tips_sequence, near_end= False, False, False
    artifacts_collected = 0
    collected_artifacts = []
    popup_index = 0
    level_complete = False
    RELOAD = Button(image=pygame.image.load("Buttons/reload_button.png").convert_alpha(), pos=(85, 43), text_input=None, font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
    PAUSE = Button(image=pygame.image.load("Buttons/pause_button.png").convert_alpha(), pos=(30, 35), text_input=None, font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color=("White"), hovering_color=("White"))
    flashlight = Flashlight(screen, intensity=100)

    while running:
        current_time = pygame.time.get_ticks()
        dt = (current_time - previous_time) / 1000.0
        previous_time = current_time
        accumulator += dt
        keys = pygame.key.get_pressed()
        MENU_MOUSE_POS = pygame.mouse.get_pos()

        for popup in popups:
            if popup.visible:
                popup_active = True
                break
            else:
                popup_active = False

        for player in active_players:
                
            for volcano in volcanoes:
                volcano.interact_with_player(player, volcanoes)

            if player.position.y > level_height + 100 or player.position.y < -100:
                player.reload(spawn_point)

            if player.on_platform == finish_line:
                reset_positions = [spawn_point] * num_of_players
                level_complete = True
                text_color = player.color
                checkpoint_increment = 0
                spawn_point = OG_spawn_point
            
                for platform in next_checkpoints:
                    platform.color = "#9ff084"
            
            if player.on_platform in death_platforms:
                player.reload(spawn_point)

            if player.on_platform == next_checkpoint:
                spawn_point = (next_checkpoint.position.x + (next_checkpoint.dimensions[0] / 2), next_checkpoint.start_position.y - next_checkpoint.dimensions[1])
                next_checkpoint.color = "#228700"
                reset_positions = [spawn_point] * num_of_players
                if checkpoint_increment < len(next_checkpoints) - 1:
                    checkpoint_increment += 1
                    next_checkpoint = next_checkpoints[checkpoint_increment]
            
            if player.on_platform == introduce_volcano and not volcano_introduction_sequence:
                for popup in popups:
                    if popup.name == "introduce_volcanoes1":
                        popup.visible = True
                volcano_introduction_sequence = True
                
            if volcano_introduction_sequence and not popups[popup_index].visible and popup_index + 1 < len(volcano_introduction):
                popups[popup_index + 1].visible = True
                popup_index += 1
            
            if player.on_platform == introduce_deathcano and not volcano_tips_sequence:
                for popup in popups:
                    if popup.name == "volcano_tip1":
                        popup.visible = True
                volcano_tips_sequence = True

            if player.on_platform == one_way and not near_end:
                for popup in popups:
                    if popup.name == "one_way_home":
                        popup.visible = True
                near_end = True

            for artifact in artifacts:
                if player.rect.colliderect(artifact.rect) and not artifact.collected and artifact not in collected_artifacts:
                    artifact.collect()
                    artifacts_collected += 1
                    collected_artifacts.append(artifact)

        for event in pygame.event.get():

            for popup in popups:
                popup.handle_event(event)

            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN and not popup_active:
                if RELOAD.checkForInput(MENU_MOUSE_POS):
                    reload_map(active_players, platforms, reset_positions, artifacts)
                    level_complete = False
                    text_color = ("#71d6f5")
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()

                if PAUSE.checkForInput(MENU_MOUSE_POS):
                    time_paused = time.time()
                    paused = True

            elif event.type == pygame.KEYDOWN and not popup_active:
                if event.key == pygame.K_r:
                    reload_map(active_players, platforms, reset_positions, artifacts)
                    level_complete = False
                    text_color = ("#71d6f5")
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()

                if event.key == pygame.K_p:
                    time_paused = time.time()
                    paused = True

        if paused:
            action = await pause_menu(screen, level_name, show_controls, window_size, time_paused)
            if action == False:
                paused = False
            elif action == "level restart":
                show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
                start_timer = pygame.time.get_ticks()
                popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in volcano_introduction + level_tips]
                artifacts_collected = 0
                collected_artifacts = []
                paused = False
            elif action == "show controls":
                show_controls = not show_controls
                paused = False
            elif action == "go to home":
                running = False
            elif action == "go to settings" and not editing_settings:
                time_entered_settings = time.time()
                paused = False
                editing_settings = True
        
        elif editing_settings:
            settings_action = await settings_menu(screen, window_size, time_entered_settings)
            if not settings_action:
                editing_settings = False
            elif isinstance(settings_action, int):
                active_players = await newPlayerCount(settings_action, active_players, level_name)
                num_of_players = len(active_players)
                editing_settings = False

        elif level_complete:
            if artifacts_collected == 3:
                action = await level_completed(screen, level_name, text_color, window_size, post_mission_briefing, time_finished=time.time())
                if action == "level restart":
                    show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
                    start_timer = pygame.time.get_ticks()
                    popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in volcano_introduction + level_tips]
                    artifacts_collected = 0
                    collected_artifacts = []
                    level_complete = False
                
                elif action == "go to home":
                    running = False
            else:
                screen.blit(print_need_artifacts, need_artifacts_rect)
        
        else:
            while accumulator >= fixed_delta_time:
                update_game_logic(fixed_delta_time, active_players, platforms, keys, spawn_point, popup_active)
                accumulator -= fixed_delta_time
            subscreens = getSplitscreenLayout(canvas, active_players)
            canvas.fill((0, 0, 0))
            renderSplitscreenLayout(canvas, active_players, num_of_players, bg_image, platforms, camera, death_platforms, artifacts, collected_artifacts, flashlight, volcanoes, subscreens)
            counting_string = update_timer(start_timer)
            render_artifact_count(("#56911f"), artifacts_collected)
            render_timer(lil_font, "#32854b", counting_string)

            for popup in popups:
                popup.update()

            for button in [RELOAD, PAUSE]:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)

            pygame.display.flip()

        await asyncio.sleep(0)

async def magnus25(active_players):
    
    level_name = 'Magnus25'
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 60)
    lil_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 30)
    text_color = ("#0c4701")

    num_of_players = len(active_players)
    show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)   

    popup_data = [

        {"name": "popup1",
        "screen": screen,
        "text": "this is a popup",
        "theme_color": text_color,
        "button_text": "ok",
        "visible": True
    },
    
        {"name": "popup2",
         "screen": screen,
         "text": "this is another popup",
         "theme_color": text_color,
         "button_text": "got it",
         "visible": False
    }]
    
    popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in popup_data]

    print_need_artifacts = font.render("you need more artifacts", True, text_color)
    need_artifacts_rect = print_need_artifacts.get_rect(center=(window_size[0] // 2, window_size[1] // 2))

    artifacts = [] # THIS IS TEMPORARY
    running = True
    fixed_delta_time = 1 / 60
    accumulator = 0
    previous_time = pygame.time.get_ticks()
    start_timer = pygame.time.get_ticks()
    paused = False
    editing_settings = False
    artifacts_collected = 0
    collected_artifacts = []
    level_complete = False
    RELOAD = Button(image=pygame.image.load("Buttons/reload_button.png").convert_alpha(), pos=(85, 43), text_input=None, font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
    PAUSE = Button(image=pygame.image.load("Buttons/pause_button.png").convert_alpha(), pos=(30, 35), text_input=None, font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color=("White"), hovering_color=("White"))
    flashlight = Flashlight(screen, intensity=100)

    while running:
        current_time = pygame.time.get_ticks()
        dt = (current_time - previous_time) / 1000.0
        previous_time = current_time
        accumulator += dt
        keys = pygame.key.get_pressed()
        MENU_MOUSE_POS = pygame.mouse.get_pos()

        for popup in popups:
            if popup.visible:
                popup_active = True
                break
            else:
                popup_active = False

        for player in active_players:
            if player.id == 1 and player.on_platform:
                current_platform = player.on_platform.name

            if player.position.y > level_height + 100:
                player.reload(spawn_point)

            if player.on_platform == finish_line:
                reset_positions = [spawn_point] * num_of_players
                level_complete = True
                text_color = player.color
                checkpoint_increment = 0
                spawn_point = OG_spawn_point
            
                for platform in next_checkpoints:
                        platform.color = "#9ff084"
            
            if player.on_platform in death_platforms:
                player.reload(spawn_point)

            if player.on_platform == next_checkpoint:
                spawn_point = (next_checkpoint.position.x + (next_checkpoint.dimensions[0] / 2), next_checkpoint.start_position.y - next_checkpoint.dimensions[1])
                next_checkpoint.color = "#228700"
                reset_positions = [spawn_point] * num_of_players
                if checkpoint_increment < len(next_checkpoints) - 1:
                    checkpoint_increment += 1
                    next_checkpoint = next_checkpoints[checkpoint_increment]

            for artifact in artifacts:
                if player.rect.colliderect(artifact.rect) and not artifact.collected and artifact not in collected_artifacts:
                    artifact.collect()
                    artifacts_collected += 1
                    collected_artifacts.append(artifact)

        for event in pygame.event.get():

            for popup in popups:
                popup.handle_event(event)

            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN and not popup_active:
                if RELOAD.checkForInput(MENU_MOUSE_POS):
                    reload_map(active_players, platforms, reset_positions, artifacts)
                    level_complete = False
                    text_color = ("#71d6f5")
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()

                if PAUSE.checkForInput(MENU_MOUSE_POS):
                    time_paused = time.time()
                    paused = True

            elif event.type == pygame.KEYDOWN and not popup_active:
                if event.key == pygame.K_r:
                    reload_map(active_players, platforms, reset_positions, artifacts)
                    level_complete = False
                    text_color = ("#71d6f5")
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()

                if event.key == pygame.K_p:
                    time_paused = time.time()
                    paused = True

        if paused:
            action = await pause_menu(screen, level_name, show_controls, window_size, time_paused)
            if action == False:
                paused = False
            elif action == "level restart":
                show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
                start_timer = pygame.time.get_ticks()
                popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in popup_data]
                artifacts_collected = 0
                collected_artifacts = []
                paused = False
            elif action == "show controls":
                show_controls = not show_controls
                paused = False
            elif action == "go to home":
                running = False
            elif action == "go to settings" and not editing_settings:
                time_entered_settings = time.time()
                paused = False
                editing_settings = True
        
        elif editing_settings:
            settings_action = await settings_menu(screen, window_size, time_entered_settings)
            if not settings_action:
                editing_settings = False
            elif isinstance(settings_action, int):
                active_players = await newPlayerCount(settings_action, active_players, level_name)
                num_of_players = len(active_players)
                editing_settings = False

        elif level_complete:
            if artifacts_collected == 3:
                action = await level_completed(screen, level_name, text_color, window_size, popup_text="Hello. Nothing here, yet :)", time_finished=time.time())
                if action == "level restart":
                    show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
                    start_timer = pygame.time.get_ticks()
                    popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in popup_data]
                    artifacts_collected = 0
                    collected_artifacts = []
                    level_complete = False
                
                elif action == "go to home":
                    running = False
            else:
                screen.blit(print_need_artifacts, need_artifacts_rect)
        
        else:
            while accumulator >= fixed_delta_time:
                update_game_logic(fixed_delta_time, active_players, platforms, keys, spawn_point, popup_active)
                accumulator -= fixed_delta_time
                for player in active_players:
                    if player.id == 1:
                        camera.update(player, num_of_players)

            screen.fill((0, 0, 0))
            counting_string = update_timer(start_timer)
            screen.blit(bg_image, (0, 0))
            render_game_objects(platforms, active_players, camera, flashlight, death_platforms, screen)
            # render_artifacts(artifacts, camera, collected_artifacts)
            # render_artifact_count(("#56911f"), artifacts_collected)
            render_timer(lil_font, "#32854b", counting_string)
            display_controls(len(active_players), show_controls, introduced_controls_state, print_player1_controls, print_player3_controls, print_player4_controls)

            for popup in popups:
                popup.update()

            for button in [RELOAD, PAUSE]:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)

            pygame.display.flip()

        await asyncio.sleep(0)

async def tutorial_level(active_players):

    from level_init import tutorialPlatformsInit

    level_name = 'Tutorial_level'
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 60)
    lil_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 25)
    text_color = ("#71d6f5")

    num_of_players = len(active_players)
    show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
    intro_to_jumping, intro_to_sliding, intro_to_jumpslide, artifacts = tutorialPlatformsInit(platforms, level_name)

    for player in active_players:
        player.can_jump, player.can_slide = False, False
        introduced_controls_state["introduced_jumping"], introduced_controls_state["introduced_sliding"] = False, False
    
    print_need_artifacts = font.render("you need more artifacts", True, text_color)
    need_artifacts_rect = print_need_artifacts.get_rect(center=(window_size[0] // 2, window_size[1] // 2))
    
    intitial_popups = [

        {"name": "welcome",
        "screen": screen,
        "text": "welcome to training",
        "theme_color": text_color,
        "button_text": "next",
        "visible": True
    },
    
        {"name": "purpose",
         "screen": screen,
         "text": "here, you will learn the basics required to go out on missions",
         "theme_color": text_color,
         "button_text": "next",
         "visible": False
    },

        {"name": "get_started",
         "screen": screen,
         "text": "to get started, walk forward",
         "theme_color": text_color,
         "button_text": "got it",
         "visible": False
    }]
    
    popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in intitial_popups]

    background_darkener = pygame.Surface((window_size[0], window_size[1]), pygame.SRCALPHA)
    background_darkener.fill((0, 0, 0, 129))

    running = True
    fixed_delta_time = 1 / 60
    accumulator = 0
    start_timer = pygame.time.get_ticks()
    previous_time = pygame.time.get_ticks()
    paused = False
    editing_settings = False
    artifacts_collected = 0
    collected_artifacts = []
    level_complete = False
    popup_index = 0
    RELOAD = Button(image=pygame.image.load("Buttons/reload_button.png").convert_alpha(), pos=(85, 43), text_input=None, font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
    PAUSE = Button(image=pygame.image.load("Buttons/pause_button.png").convert_alpha(), pos=(30, 35), text_input=None, font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color=("White"), hovering_color=("White"))
    flashlight = Flashlight(screen, intensity=100)

    while running:
        current_time = pygame.time.get_ticks()
        dt = (current_time - previous_time) / 1000.0
        previous_time = current_time
        accumulator += dt
        keys = pygame.key.get_pressed()
        MENU_MOUSE_POS = pygame.mouse.get_pos()
        update_tutorial_controls(active_players, intro_to_jumping, intro_to_sliding, introduced_controls_state)

        for popup in popups:
            if popup.visible:
                popup_active = True
                break
            else:
                popup_active = False

        if not popups[popup_index].visible and popup_index + 1 < len(intitial_popups):
            popups[popup_index + 1].visible = True
            popup_index += 1

        for player in active_players:
            if player.id == 1 and player.on_platform:
                current_platform = player.on_platform.name

            blit_jumpslide = player.on_platform == intro_to_jumpslide

            if player.position.y > level_height + 100:
                player.reload(spawn_point)

            if player.on_platform == finish_line:
                reset_positions = [spawn_point] * num_of_players
                level_complete = True
                text_color = player.color
                checkpoint_increment = 0
                spawn_point = OG_spawn_point

                introduced_controls_state["introduced_jumping"], introduced_controls_state['introduced_sliding'] = False, False
                
                for platform in next_checkpoints:
                    platform.color = "#9ff084"
                for player in active_players:
                    player.can_jump, player.can_slide = False, False

            if player.on_platform in death_platforms:
                player.reload(spawn_point)

            if player.on_platform == next_checkpoint:
                spawn_point = (next_checkpoint.position.x + (next_checkpoint.dimensions[0] / 2), next_checkpoint.start_position.y - next_checkpoint.dimensions[1])
                next_checkpoint.color = "#228700"
                reset_positions = [spawn_point] * num_of_players
                if checkpoint_increment < len(next_checkpoints) - 1:
                    checkpoint_increment += 1
                    next_checkpoint = next_checkpoints[checkpoint_increment]

            for artifact in artifacts:
                if player.rect.colliderect(artifact.rect) and not artifact.collected and artifact not in collected_artifacts:
                    artifact.collect()
                    artifacts_collected += 1
                    collected_artifacts.append(artifact)

        for event in pygame.event.get():

            for popup in popups:
                popup.handle_event(event)

            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN and not popup_active:
                if RELOAD.checkForInput(MENU_MOUSE_POS):
                    reload_map(active_players, platforms, reset_positions, artifacts)
                    level_complete = False
                    text_color = ("#71d6f5")
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()

                if PAUSE.checkForInput(MENU_MOUSE_POS):
                    time_paused = time.time()
                    paused = True

            elif event.type == pygame.KEYDOWN and not popup_active:
                if event.key == pygame.K_r:
                    reload_map(active_players, platforms, reset_positions, artifacts)
                    level_complete = False
                    text_color = ("#71d6f5")
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()

                if event.key == pygame.K_p:
                    time_paused = time.time()
                    paused = True

        if paused:
            action = await pause_menu(screen, level_name, show_controls, window_size, time_paused)
            if action == False:
                paused = False
            elif action == "level restart":
                show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
                intro_to_jumping, intro_to_sliding, intro_to_jumpslide, artifacts = tutorialPlatformsInit(platforms, level_name)
                start_timer = pygame.time.get_ticks()
                popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in intitial_popups]
                popup_index, artifacts_collected = 0, 0
                collected_artifacts = []
                for player in active_players:
                    player.can_jump, player.can_slide = False, False
                    introduced_controls_state["introduced_jumping"], introduced_controls_state["introduced_sliding"] = False, False
                paused = False
            elif action == "go to home":
                running = False
            elif action == "go to settings" and not editing_settings:
                time_entered_settings = time.time()
                paused = False
                editing_settings = True

        elif editing_settings:
            settings_action = await settings_menu(screen, window_size, time_entered_settings)
            if not settings_action:
                editing_settings = False
            elif isinstance(settings_action, int):
                active_players = await newPlayerCount(settings_action, active_players, level_name)
                num_of_players = len(active_players)
                for player in active_players:
                    player.can_jump, player.can_slide = False, False
                    introduced_controls_state["introduced_jumping"], introduced_controls_state["introduced_sliding"] = False, False
                editing_settings = False

        elif level_complete:
            if artifacts_collected == 3:
                action = await level_completed(screen, level_name, text_color, window_size, popup_text="Hello. Nothing here, yet :)", time_finished=time.time())
                if action == "level restart":
                    show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
                    intro_to_jumping, intro_to_sliding, intro_to_jumpslide, artifacts = tutorialPlatformsInit(platforms, level_name)
                    start_timer = pygame.time.get_ticks()
                    popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in intitial_popups]
                    popup_index, artifacts_collected = 0, 0
                    collected_artifacts = []
                    for player in active_players:
                        player.can_jump, player.can_slide = False, False
                        introduced_controls_state["introduced_jumping"], introduced_controls_state["introduced_sliding"] = False, False
                    level_complete = False
                elif action == "go to home":
                    running = False
            else:
                screen.blit(print_need_artifacts, need_artifacts_rect)

        else:
            while accumulator >= fixed_delta_time:
                update_game_logic(fixed_delta_time, active_players, platforms, keys, spawn_point, popup_active)
                accumulator -= fixed_delta_time
            
            # Determine the layout dynamically based on the number of active players
            subscreens = getSplitscreenLayout(canvas, active_players)

            # Clear the canvas
            canvas.fill((0, 0, 0))  # Fill the canvas with black

            # Render game objects for each active player's view
            renderSplitscreenLayout(canvas, active_players, num_of_players, bg_image, platforms, camera, death_platforms, artifacts, collected_artifacts, flashlight, volcanoes=None, subscreens=subscreens)

            counting_string = update_timer(start_timer)
            render_artifact_count(("#56911f"), artifacts_collected)
            render_timer(lil_font, "#32854b", counting_string)
            display_controls(len(active_players), show_controls, introduced_controls_state, print_player1_controls, print_player3_controls, print_player4_controls)
            introduce_controls(blit_jumpslide)

            for popup in popups:
                popup.update()

            for button in [RELOAD, PAUSE]:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)

            pygame.display.flip()

        await asyncio.sleep(0)

async def main():

    from level_init import mainTextInit

    current_weather = await game_init()
    weather_codes = await load_json_file('weather_codes.json')

    weather_condition = next(
        (condition for condition, codes in weather_codes['weather-codes'].items() if current_weather['weather_code'] in codes),
        None
    )

    level_name = 'Home'
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 60)
    lil_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 25)
    text_color = "#71d6f5"

    num_of_players = 1
    show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)

    show_settings = next((platform for platform in platforms if platform.name == 'settings'), None)

    artifact_image1 = pygame.image.load("Levels/Terus1/assets/artifact1.png")
    artifact_data = [
        {"image": artifact_image1, "position": (900, 1480), "name": "Golden Idol"},
        {"image": artifact_image1, "position": (500, 450), "name": "Ancient Vase"}
    ]
    artifacts = pygame.sprite.Group(Artifact(data["image"], data["position"], data["name"]) for data in artifact_data)

    title_screen_text = mainTextInit(font, lil_font, text_color, window_size)

    running = True
    fixed_delta_time = 1 / 60
    accumulator = 0
    previous_time = pygame.time.get_ticks()
    paused = False
    editing_settings = False
    reload_players = False
    platforms_used = []
    flashlight = Flashlight(screen, intensity=100)
    RELOAD = Button(image=pygame.image.load("Buttons/reload_button.png").convert_alpha(), pos=(85, 43), text_input=None, font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
    PAUSE = Button(image=pygame.image.load("Buttons/pause_button.png").convert_alpha(), pos=(30, 35), text_input=None, font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color="White", hovering_color="White")

    while running:
        current_time = pygame.time.get_ticks()
        dt = (current_time - previous_time) / 1000.0
        previous_time = current_time
        accumulator += dt
        keys = pygame.key.get_pressed()
        MENU_MOUSE_POS = pygame.mouse.get_pos()

        for player in active_players:
            if player.id == 1:
                if player.on_platform:
                    current_platform = player.on_platform.name
                    if current_platform not in platforms_used:
                        platforms_used.append(current_platform)
                # print(player.position)

            if player.position.y > level_height + 100:
                player.reload(OG_spawn_point)
                await tutorial_level(active_players)

            if player.on_platform == show_settings and not editing_settings:
                if not reload_players:
                    time_entered_settings = time.time()
                    editing_settings = True
                else:
                    player.reload(spawn_point)
                    reload_players = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if RELOAD.checkForInput(MENU_MOUSE_POS):
                    reload_map(active_players, platforms, reset_positions, artifacts)
                    text_color = "#71d6f5"

                if PAUSE.checkForInput(MENU_MOUSE_POS):
                    time_paused = time.time()
                    paused = True

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_1:
                    await terus1(active_players, weather_condition)
                
                if event.key == pygame.K_2:
                    await scopulosus53(active_players)
                
                if event.key == pygame.K_3:
                    await magnus25(active_players)

                if event.key == pygame.K_r:
                    reload_map(active_players, platforms, reset_positions, artifacts)
                    text_color = "#71d6f5"

                if event.key == pygame.K_p:
                    time_paused = time.time()
                    paused = True

                elif paused:
                    if event.key == pygame.K_u or not pause_menu(screen, level_name, show_controls, window_size, time_paused):
                        paused = False
                    elif event.key == pygame.K_r:
                        reload_map(active_players, platforms, reset_positions, artifacts)
                        paused = False
                        text_color = "#71d6f5"

        if paused:
            action = await pause_menu(screen, level_name, show_controls, window_size, time_paused)
            if action == False:
                paused = False
            elif action == "level restart":
                show_controls, bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
                paused = False
            elif action == "go to home":
                paused = False
            elif action == "go to settings" and not editing_settings:
                time_entered_settings = time.time()
                paused = False
                editing_settings = True

        elif editing_settings:
            settings_action = await settings_menu(screen, window_size, time_entered_settings)
            if not settings_action:
                reload_players = True
                editing_settings = False
            elif isinstance(settings_action, int):
                active_players = await newPlayerCount(settings_action, active_players, level_name)
                num_of_players = len(active_players)
                editing_settings = False

        else:
            while accumulator >= fixed_delta_time:
                update_game_logic(fixed_delta_time, active_players, platforms, keys, spawn_point, popup_active=False)
                accumulator -= fixed_delta_time

            screen.fill((0, 0, 0))
            screen.blit(bg_image, (0, 0))
            screen.blit(title_screen_text, (0, 0))
            render_game_objects(platforms, active_players, camera, flashlight, death_platforms=[], surface=screen)
            display_controls(len(active_players), show_controls, introduced_controls_state, print_player1_controls, print_player3_controls, print_player4_controls)

            for button in [RELOAD, PAUSE]:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)

            pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()

# # Run the main function
asyncio.run(main())

# Debugging and profiling code
# import pstats, cProfile

# if __name__ == "__main__":
#     # Use cProfile to profile the main function
#     profiler = cProfile.Profile()
#     profiler.enable()

#     asyncio.run(main())

#     profiler.disable()
#     profiler.print_stats(sort="cumtime")
#     profiler.dump_stats("profile_data.prof")
#     stats = pstats.Stats("profile_data.prof")
#     stats.strip_dirs().sort_stats("cumtime").print_stats(20)


"""if you read this you are nice"""