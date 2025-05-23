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
from Levels.Terus1.flashlight import Flashlight
from Players.player import Player
from camera import Camera
from artifacts import Artifact
from popups import Popup
from Buttons.buttons import Button
from game_init import (
    getArtifacts,
    render_artifacts,
    centerText,
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
    platform.document.body.style.background = "#1d2d4b"

screen.fill("#020626")
loading_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 50)
loading_text = loading_font.render("loading...", True, ("#71d6f5"))
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

    return bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint

async def newPlayerCount(new_num_of_players ,active_players, level_name):
    if len(active_players) != new_num_of_players:
        num_of_players = new_num_of_players
        bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
    return active_players

async def settings_menu(screen, window_size, time_entered_settings):

    blur_duration = 0
    max_blur_radius = 6
    screen_surface = pygame.image.tobytes(screen, "RGBA")
    pil_image = Image.frombytes("RGBA", screen.get_size(), screen_surface)

    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 55)
    lil_font = pygame.font.Font('fonts/pixelated.ttf', 35)
    button_image = pygame.image.load("Buttons/tutorial_button.png").convert_alpha()
    small_button = pygame.image.load("Buttons/lilbutton.png").convert_alpha()

    EXIT_SETTINGS = Button(image=button_image, pos=(500, 500), text_input="Exit", font=pygame.font.Font('fonts/pixelated.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
    ONE_PLAYER = Button(image=small_button, pos=(470, 250), text_input="1p", font=pygame.font.Font('fonts/pixelated.ttf', 25), base_color="#167fc9", hovering_color="#F59071")
    TWO_PLAYER = Button(image=small_button, pos=(550, 250), text_input="2p", font=pygame.font.Font('fonts/pixelated.ttf', 25), base_color="#167fc9", hovering_color="#F59071")
    THREE_PLAYER = Button(image=small_button, pos=(630, 250), text_input="3p", font=pygame.font.Font('fonts/pixelated.ttf', 25), base_color="#167fc9", hovering_color="#F59071")
    FOUR_PLAYER = Button(image=small_button, pos=(710, 250), text_input="4p", font=pygame.font.Font('fonts/pixelated.ttf', 25), base_color="#167fc9", hovering_color="#F59071")

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

async def pause_menu(screen, level_name, window_size, time_paused):

    blur_duration = 0
    max_blur_radius = 10
    screen_surface = pygame.image.tobytes(screen, "RGBA")
    pil_image = Image.frombytes("RGBA", screen.get_size(), screen_surface)

    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 55)
    button_image = pygame.image.load("Buttons/tutorial_button.png").convert_alpha()

    printtext = font.render("Paused", True, ("#71d6f5"))
    text_rect = printtext.get_rect(center=(window_size[0] // 2, window_size[1] // 2 - 200))

    RESUME_BUTTON = Button(image=button_image, pos=(500, 260), text_input="Resume", font=pygame.font.Font('fonts/pixelated.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
    RESTART_LEVEL = Button(image=button_image, pos=(500, 330), text_input="Restart", font=pygame.font.Font('fonts/pixelated.ttf', 40), base_color="#167fc9", hovering_color="#F59071")

    if level_name in ["Home", "Training"]:
        
        SETTINGS = Button(image=button_image, pos=(500, 400), text_input="Settings", font=pygame.font.Font('fonts/pixelated.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
        MAIN_MENU = Button(image=button_image, pos=(500, 470), text_input="Home", font=pygame.font.Font('fonts/pixelated.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
        buttons = [RESUME_BUTTON, RESTART_LEVEL, SETTINGS, MAIN_MENU]
    
    else:

        SETTINGS = Button(image=button_image, pos=(500, 400), text_input="Settings", font=pygame.font.Font('fonts/pixelated.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
        MAIN_MENU = Button(image=button_image, pos=(500, 540), text_input="Home", font=pygame.font.Font('fonts/pixelated.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
        LEVEL_SELECTION = Button(image=button_image, pos=(500, 470), text_input="Level select", font=pygame.font.Font('fonts/pixelated.ttf', 30), base_color="#167fc9", hovering_color="#F59071")
        buttons = [RESUME_BUTTON, RESTART_LEVEL, SETTINGS, LEVEL_SELECTION, MAIN_MENU]

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

                if level_name not in ["Home", "Training"]:

                    if LEVEL_SELECTION.checkForInput(MENU_MOUSE_POS):
                        return "go to level select"

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

async def level_completed(screen, level_name, text_color, window_size, popup_text, time_finished, total_time):
    
    blur_duration = 0
    max_blur_radius = 10
    screen_surface = pygame.image.tobytes(screen, "RGBA")
    pil_image = Image.frombytes("RGBA", screen.get_size(), screen_surface)

    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 55)
    lil_font = pygame.font.Font('fonts/pixelated.ttf', 40)
    button_image = pygame.image.load("Buttons/tutorial_button.png").convert_alpha()

    printtext = font.render(f"{level_name} complete!", True, text_color)
    printtime = lil_font.render(f"Time: {total_time}", True, text_color)
    text_rect = printtext.get_rect(center=(window_size[0] // 2, window_size[1] // 2 - 200))
    time_rect = printtime.get_rect(center=(window_size[0] // 2, 500))
    hovering_color = "#F59071"

    artifact_information = Popup(name="artifact_info", screen=screen, text=popup_text, theme_color=text_color, button_text="cool", visible=False)
    where_level_select = Popup(name="level_selection", screen=screen, text="in the homescreen, press l or stand on the green platform and press enter to enter level selection.", theme_color=text_color, button_text="got it", visible=False)
    popups = [artifact_information, where_level_select]

    artifact_information.font_size, artifact_information.max_line_length = 23, 40

    RESTART_LEVEL = Button(image=button_image, pos=(395, 295), text_input="restart", font=pygame.font.Font('fonts/pixelated.ttf', 25), base_color=text_color, hovering_color=hovering_color)
    ARTIFACT_INFO = Button(image=button_image, pos=(605, 295), text_input="artifact info", font=pygame.font.Font('fonts/pixelated.ttf', 25), base_color=text_color, hovering_color=hovering_color)
    LEVEL_SELECT = Button(image=button_image, pos=(395, 365), text_input="level select", font=pygame.font.Font('fonts/pixelated.ttf', 25), base_color=text_color, hovering_color=hovering_color)
    MAIN_MENU = Button(image=button_image, pos=(605, 365), text_input="home", font=pygame.font.Font('fonts/pixelated.ttf', 40), base_color=text_color, hovering_color=hovering_color)
    buttons = [RESTART_LEVEL, ARTIFACT_INFO, LEVEL_SELECT, MAIN_MENU]

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
            
            for popup in popups:
                popup.handle_event(event)

            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.MOUSEBUTTONDOWN and not artifact_information.visible and not where_level_select.visible:
                
                if RESTART_LEVEL.checkForInput(MENU_MOUSE_POS):
                    return "level restart"
                
                elif ARTIFACT_INFO.checkForInput(MENU_MOUSE_POS):
                    artifact_information.visible = True

                elif LEVEL_SELECT.checkForInput(MENU_MOUSE_POS):
                    if level_name == "Training":
                        where_level_select.visible = True
                    else:
                        return "go to level select"
                
                elif MAIN_MENU.checkForInput(MENU_MOUSE_POS):
                    return "go to home"

        screen.blit(blurred_surface, (0, 0))
        
        if time_elapsed >= blur_duration:
            screen.blit(printtext, text_rect)
            screen.blit(printtime, time_rect)
            
            for button in buttons:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)
            
            for popup in popups:
                popup.update()

        pygame.display.flip()
        await asyncio.sleep(0)

async def levelSelect(active_players):
    
    bg_image = pygame.image.load("assets/levelSelect/stars_bg.png").convert_alpha()
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40)
    lil_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 30)
    button_image = pygame.image.load("Buttons/tutorial_button.png").convert_alpha()

    level1 = pygame.image.load("assets/levelSelect/Terus1.png").convert_alpha()
    level1_text = font.render("1. Terus1", True, ("#116da6"))

    level2 = pygame.image.load("assets/levelSelect/Scopulosus53.png").convert_alpha()
    level2_text = font.render("2. scopulosus53", True, ("#cc6c33"))

    level3 = pygame.image.load("assets/levelSelect/Magnus25.png").convert_alpha()
    level3_text = font.render("3. Magnus25", True, ("#1d806b"))

    level_images = [level1, level2, level3]
    level_texts = [level1_text, level2_text, level3_text]
    LEVELS = [terus1, scopulosus53, magnus25]
    
    HOME = Button(image=button_image, pos=(125, 48), text_input="home", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color="#000000", hovering_color="#F59071")
    PLAY = Button(image=button_image, pos=(335, 48), text_input="play", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 35), base_color="#000000", hovering_color="#F59071")
    BACK = Button(image=pygame.image.load("assets/gameControls/backward.png").convert_alpha(), pos=(250, 350), text_input=None, font=font, base_color="#ffffff", hovering_color="#ffffff")
    FORWARD = Button(image=pygame.image.load("assets/gameControls/forward.png").convert_alpha(), pos=(750, 335), text_input=None, font=font, base_color="#ffffff", hovering_color="#ffffff")
    buttons = [HOME, PLAY, BACK, FORWARD]

    select = pygame.image.load("assets/gameControls/keyboard_enter.png").convert_alpha()
    left_normal = pygame.image.load("assets/gameControls/keyboard_arrow_left.png").convert_alpha()
    left_outline = pygame.image.load("assets/gameControls/keyboard_arrow_left_outline.png").convert_alpha()
    right_normal = pygame.image.load("assets/gameControls/keyboard_arrow_right.png").convert_alpha()
    right_outline = pygame.image.load("assets/gameControls/keyboard_arrow_right_outline.png").convert_alpha()

    current_level = 0
    running = True

    while running:
        
        screen.blit(bg_image, (0, 0))

        level_img = level_images[current_level]
        level_text = level_texts[current_level]

        screen.blit(level_img, (0, 0))
        screen.blit(level_text, centerText(level_text, (500, 130)))

        keys = pygame.key.get_pressed()
        left = left_outline if keys[pygame.K_LEFT] else left_normal
        right = right_outline if keys[pygame.K_RIGHT] else right_normal

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    if current_level > 0:
                        current_level -= 1
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    if current_level < len(level_images) - 1:
                        current_level += 1
                elif event.key == pygame.K_RETURN:
                    output = await LEVELS[current_level](active_players)
                    if output == False:
                        running = output
                elif event.key == pygame.K_h or event.key == pygame.K_ESCAPE:
                    running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if HOME.checkForInput(pygame.mouse.get_pos()):
                    running = False
                elif PLAY.checkForInput(pygame.mouse.get_pos()):
                    output = await LEVELS[current_level](active_players)
                    if output == False:
                        running = output
                elif FORWARD.checkForInput(pygame.mouse.get_pos()):
                    if current_level < len(level_images) - 1:
                        current_level += 1
                elif BACK.checkForInput(pygame.mouse.get_pos()):
                    if current_level > 0:
                        current_level -= 1

        screen.blit(left, (10, 635))
        screen.blit(right, (70, 635))
        screen.blit(select, (140, 635))
        for button in buttons:
            button.changeColor(pygame.mouse.get_pos())
            button.update(screen)
        
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

async def terus1(active_players):

    screen.fill("#020626")
    loading_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40)
    loading_text = loading_font.render("Loading...", True, ("#71d6f5"))
    loading_rect = loading_text.get_rect(center=(window_size[0] // 2, window_size[1] // 2))
    screen.blit(loading_text, loading_rect)
    pygame.display.update()

    from level_init import terusPlatformsInit

    level_name = 'Terus1'
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 60)
    lil_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 30)
    text_color = ("#116da6")
    magnetite_information = await load_json_file(f"Levels/{level_name}/artifact_info.json")
    post_mission_briefing = magnetite_information['magnetite-info']['after-level-info']

    num_of_players = len(active_players)
    bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)   
    show_slide, show_slide2, show_checkpoint1_reached, show_checkpoint2_reached, brighten_scene, artifacts = terusPlatformsInit(platforms, level_name)

    popup_data = [

        {"name": "introduce_flashlight",
        "screen": screen,
        "text": "Press 'f' to use the flashlight. Keep in mind that only one player can use the flashlight.",
        "theme_color": text_color,
        "button_text": "ok",
        "visible": True
    },
    
        {"name": "flashlight_broken",
         "screen": screen,
         "text": "It looks like the flashlight is facing external interference! Better hurry...",
         "theme_color": text_color,
         "button_text": "got it",
         "visible": False
    }]
    
    popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in popup_data]
    
    for popup in popups:
        
        if popup.name == "pre_mission_briefing":
            popup.max_line_length = 50
            popup.font_size = 20

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

                flashlight = Flashlight(screen, intensity=60)
                flashlight.enabled = True
                flashlight_broken = True

            if player.position.y > level_height + 100:
                player.reload(spawn_point)

            if player.on_platform == finish_line:
                
                level_complete = True
                checkpoint_increment = 0
                spawn_point = OG_spawn_point

            elif player.on_platform in death_platforms:
                player.reload(spawn_point)

            if player.on_platform == next_checkpoint:
                spawn_point = (next_checkpoint.position.x + (next_checkpoint.dimensions[0] / 2), next_checkpoint.start_position.y - next_checkpoint.dimensions[1])
                next_checkpoint.color = "#228700"
                
                
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
                    reload_map(active_players, platforms, spawn_point, artifacts)
                    level_complete = False
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()

                if PAUSE.checkForInput(MENU_MOUSE_POS):
                    time_paused = time.time()
                    paused = True
            
            elif event.type == pygame.KEYDOWN and not popup_active:
                
                if event.key == pygame.K_f:
                    flashlight.on = not flashlight.on

                if event.key == pygame.K_r:
                    reload_map(active_players, platforms, spawn_point, artifacts)  
                    level_complete = False
                    flashlight.enabled = True
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()
                
                if event.key == pygame.K_p:
                    time_paused = time.time()
                    paused = True

        if paused:
            action = await pause_menu(screen, level_name, window_size, time_paused)
            
            if action == False:
                paused = False
            
            elif action == "level restart":
                bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
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
                return False
            
            elif action == "go to settings" and not editing_settings:
                time_entered_settings = time.time()
                paused = False
                editing_settings = True
            
            elif action == "go to level select":
                running = False

        elif editing_settings:
            settings_action = await settings_menu(screen, window_size, time_entered_settings)
            if not settings_action:
                editing_settings = False
            elif isinstance(settings_action, int):
                active_players = await newPlayerCount(settings_action, active_players, level_name)
                num_of_players = len(active_players)
                editing_settings = False

        elif level_complete:
            action = await level_completed(screen, level_name, text_color, window_size, post_mission_briefing, time_finished=time.time(), total_time=counting_string)

            if action == "level restart":
                bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
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

            elif action == "go to level select":
                running = False
            
            elif action == "go to home":
                return False

        else:
            while accumulator >= fixed_delta_time:
                update_game_logic(fixed_delta_time, active_players, platforms, keys, spawn_point, popup_active, ladders=[], hooks=[])
                accumulator -= fixed_delta_time
                flashlight.pos = pygame.Vector2(player.rect.center)

            subscreens = getSplitscreenLayout(canvas, active_players)
            canvas.fill((0, 0, 0))
            renderSplitscreenLayout(canvas, active_players, num_of_players, bg_image, platforms, camera, death_platforms, artifacts, collected_artifacts, flashlight, volcanoes=None, subscreens=subscreens, ladders=None, hooks=None)
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
                
            for button in [RELOAD, PAUSE]:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)

            pygame.display.flip()

        await asyncio.sleep(0)

async def scopulosus53(active_players):
    
    screen.fill("#020626")
    loading_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40)
    loading_text = loading_font.render("Loading...", True, ("#71d6f5"))
    loading_rect = loading_text.get_rect(center=(window_size[0] // 2, window_size[1] // 2))
    screen.blit(loading_text, loading_rect)
    pygame.display.update()

    from Levels.Scopulosus53.volcanoes import Volcano
    from level_init import scopulosusPlatformsInit

    level_name = 'Scopulosus53'
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 60)
    lil_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 30)
    text_color = ("#f70c0c")
    num_of_players = len(active_players)
    bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)   
    introduce_volcano, introduce_deathcano, one_way, artifacts = scopulosusPlatformsInit(level_name, platforms)
    carbon_nanotube_info = await load_json_file(f"Levels/{level_name}/artifact_info.json")
    post_mission_briefing = carbon_nanotube_info["carbon-nanotube-info"]["after-level-info"]

    volcano_introduction = [
    
        {"name": "introduce_volcanoes1",
         "screen": screen,
         "text": "This is a volcano.",
         "theme_color": text_color,
         "button_text": "Next",
         "visible": False
    },
    
        {"name": "introduce_volcanoes2",
         "screen": screen,
         "text": "They can be dangerous, but can also be used to your advantage.",
         "theme_color": text_color,
         "button_text": "Next",
         "visible": False
    },

        {"name": "introduce_volcanoes3",
         "screen": screen,
         "text": "Use the steam to reach higher platforms.",
         "theme_color": text_color,
         "button_text": "I'll try it",
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
            "text": "Looks like theres only one way to go now →",
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
                
                level_complete = True
                checkpoint_increment = 0
                spawn_point = OG_spawn_point
            
                for platform in next_checkpoints:
                    platform.color = "#9ff084"
            
            if player.on_platform in death_platforms:
                player.reload(spawn_point)

            if player.on_platform == next_checkpoint:
                spawn_point = (next_checkpoint.position.x + (next_checkpoint.dimensions[0] / 2), next_checkpoint.start_position.y - next_checkpoint.dimensions[1])
                next_checkpoint.color = "#228700"
                
                if checkpoint_increment < len(next_checkpoints) - 1:
                    checkpoint_increment += 1
                    next_checkpoint = next_checkpoints[checkpoint_increment]
            
            if player.on_platform == introduce_volcano and not volcano_introduction_sequence:
                for popup in popups:
                    if popup.name == "introduce_volcanoes1":
                        popup.visible = True
                volcano_introduction_sequence = True

            print(volcano_introduction_sequence, popups[popup_index].visible, popup_index + 1 < len(volcano_introduction))  
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
                    reload_map(active_players, platforms, spawn_point, artifacts)
                    level_complete = False
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()

                if PAUSE.checkForInput(MENU_MOUSE_POS):
                    time_paused = time.time()
                    paused = True

            elif event.type == pygame.KEYDOWN and not popup_active:
                if event.key == pygame.K_r:
                    reload_map(active_players, platforms, spawn_point, artifacts)
                    level_complete = False
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()

                if event.key == pygame.K_p:
                    time_paused = time.time()
                    paused = True

        if paused:
            action = await pause_menu(screen, level_name, window_size, time_paused)
            if action == False:
                paused = False
            elif action == "level restart":
                bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
                introduce_volcano, introduce_deathcano, one_way, artifacts = scopulosusPlatformsInit(level_name, platforms)
                start_timer = pygame.time.get_ticks()
                popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in volcano_introduction + level_tips]
                artifacts_collected = 0
                collected_artifacts = []
                volcano_introduction_sequence, volcano_tips_sequence, near_end= False, False, False
                popup_index = 0

                paused = False
            elif action == "go to home":
                return False
            elif action == "go to level select":
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
            action = await level_completed(screen, level_name, text_color, window_size, post_mission_briefing, time_finished=time.time(), total_time=counting_string)
            if action == "level restart":
                bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
                introduce_volcano, introduce_deathcano, one_way, artifacts = scopulosusPlatformsInit(level_name, platforms)
                start_timer = pygame.time.get_ticks()
                popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in volcano_introduction + level_tips]
                artifacts_collected = 0
                collected_artifacts = []
                volcano_introduction_sequence, volcano_tips_sequence, near_end= False, False, False
                popup_index = 0

                level_complete = False
            
            elif action == "go to level select":
                running = False
            
            elif action == "go to home":
                return False
        
        else:
            while accumulator >= fixed_delta_time:
                update_game_logic(fixed_delta_time, active_players, platforms, keys, spawn_point, popup_active, ladders=[], hooks=[])
                accumulator -= fixed_delta_time
            subscreens = getSplitscreenLayout(canvas, active_players)
            canvas.fill((0, 0, 0))
            renderSplitscreenLayout(canvas, active_players, num_of_players, bg_image, platforms, camera, death_platforms, artifacts, collected_artifacts, flashlight, volcanoes, subscreens=subscreens, ladders=None, hooks=None)
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
    
    screen.fill("#020626")
    loading_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40)
    loading_text = loading_font.render("loading...", True, ("#71d6f5"))
    loading_rect = loading_text.get_rect(center=(window_size[0] // 2, window_size[1] // 2))
    screen.blit(loading_text, loading_rect)
    pygame.display.update()
    
    from Levels.Magnus25.ladder import Ladder
    from Levels.Magnus25.hook import Hook
    from Levels.Magnus25.storm import Storm

    level_name = 'Magnus25'
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 60)
    lil_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 30)
    text_color = ("#1d806b")

    aerogel_info = await load_json_file(f"Levels/{level_name}/artifact_info.json")
    post_mission_briefing = aerogel_info["aerogel-info"]["after-level-info"]

    num_of_players = len(active_players)
    bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)   

    intro_popups = [

        {"name": "popup1",
        "screen": screen,
        "text": "This is Magnus-25. This planet is abandoned as it contains no traces of living organisms, but there are old rusted sectors where something big was built, perhaps a spaceship.",
        "theme_color": text_color,
        "button_text": "Uh huh",
        "visible": True
    },
    
        {"name": "popup2",
         "screen": screen,
         "text": " We have records of Aerogel falling down here. It is a very light and strong material. It is used in the construction of spaceships.",
         "theme_color": text_color,
         "button_text": "Got it",
         "visible": False
    },
    
        {"name": "popup3",
         "screen": screen,
         "text": "Aerogel is important to our machine as its a very good insulator, important to keep the heat in our machine from destroying other parts of the machine.",
         "theme_color": text_color,
         "button_text": "Alright",
         "visible": False
        }
    ]

    platform_popups = [
    
    {
        "name": "bunkerintro",
        "screen": screen,
        "text": "On this planet, there are many sandstorms that come with the planet being abandoned. You must find shelter in the bunkers to survive.",
        "theme_color": text_color,
        "button_text": "Got it",
        "visible": False
    },

    {
        "name": "hookIntro",
        "screen": screen,
        "text": "These are hooks that can be used to swing across large gaps. You will automatically attach, and can jump to get off.",
        "theme_color": text_color,
        "button_text": "Got it",
        "visible": False
    }
    ]
    ladder_data = [

        {
            "x-position": 1900,
            "y-position": 305,
            "height": 150,
        },

        {
            "x-position": 2110,
            "y-position": 305,  
            "height": 150,
        },

        {
            "x-position": 3990,
            "y-position": 290,  
            "height": 460,  
        },

        {
            "x-position": 4500,
            "y-position": 290,
            "height": 160,
        },

        {
            "x-position": 6290,
            "y-position": 1650,
            "height": 500,
        }
    ]

    hook_data = [
        
        {
            "x-position": 1450,
            "y-position": 200,
            "length": 250,
            "angle": 45,
            "speed": 4
        },
        
        {
            "x-position": 2655,
            "y-position": 125,
            "length": 350,
            "angle": 45,
            "speed": 4
        },

        {
            "x-position": 4950,
            "y-position": 200,
            "length": 300,
            "angle": 45,
            "speed": 5
        },

        {
            "x-position": 5850,
            "y-position": 200,
            "length": 300,
            "angle": 45,
            "speed": 4
        },

        {
            "x-position": 6540,
            "y-position": 1450,
            "length": 300,
            "angle": 45,
            "speed": 4
        }
    ]
    
    increment_num = 1
    storm_activators = []
    for platform in platforms:
        if platform.name == f"homeless-shelter{increment_num}":
            if increment_num == 1:
                introduceBunker = platform
            storm_activators.append(platform)
            increment_num += 1

        elif platform.name == "base-platform13":
            introduceHook = platform

    hooks = [Hook(data["x-position"], data["y-position"], data["length"], data["angle"], data["speed"], None) for data in hook_data]
    ladders = [Ladder(data["x-position"], data["y-position"], data["height"]) for data in ladder_data]
    popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in intro_popups + platform_popups]


    artifacts = getArtifacts(platforms, level_name)
    running = True
    fixed_delta_time = 1 / 60
    accumulator = 0
    previous_time = pygame.time.get_ticks()
    start_timer = pygame.time.get_ticks()
    paused = False
    editing_settings = False
    introduced_bunker = False
    introduced_hook = False
    artifacts_collected = 0
    collected_artifacts = []
    popup_index = 0
    level_complete = False
    RELOAD = Button(image=pygame.image.load("Buttons/reload_button.png").convert_alpha(), pos=(85, 43), text_input=None, font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color="#167fc9", hovering_color="#F59071")
    PAUSE = Button(image=pygame.image.load("Buttons/pause_button.png").convert_alpha(), pos=(30, 35), text_input=None, font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40), base_color=("White"), hovering_color=("White"))
    flashlight = Flashlight(screen, intensity=100)
    storm = Storm(trigger_distance=150, platforms=storm_activators, font=font, screen_size=(800, 600))

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

        if not popups[popup_index].visible and popup_index + 1 < len(intro_popups):
            popups[popup_index + 1].visible = True
            popup_index += 1

        for player in active_players:
            storm.update(player, spawn_point, current_time=time.time())

            if player.position.y > level_height + 100:
                player.reload(spawn_point)

            if player.on_platform == finish_line:
                
                level_complete = True
                checkpoint_increment = 0
                spawn_point = OG_spawn_point
            
                for platform in next_checkpoints:
                        platform.color = "#9ff084"
            
            if player.on_platform in death_platforms:
                player.reload(spawn_point)

            if player.on_platform == next_checkpoint:
                spawn_point = (next_checkpoint.position.x + (next_checkpoint.dimensions[0] / 2), next_checkpoint.start_position.y - next_checkpoint.dimensions[1])
                next_checkpoint.color = "#228700"
                
                if checkpoint_increment < len(next_checkpoints) - 1:
                    checkpoint_increment += 1
                    next_checkpoint = next_checkpoints[checkpoint_increment]

            if player.on_platform == introduceBunker and not introduced_bunker:
                for popup in popups:
                    if popup.name == "bunkerintro":
                        popup.visible = True
                introduced_bunker = True
            
            elif player.on_platform == introduceHook and not introduced_hook:
                for popup in popups:
                    if popup.name == "hookIntro":
                        popup.visible = True
                introduced_hook = True

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
                    reload_map(active_players, platforms, spawn_point, artifacts)
                    level_complete = False
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()

                if PAUSE.checkForInput(MENU_MOUSE_POS):
                    time_paused = time.time()
                    paused = True

            elif event.type == pygame.KEYDOWN and not popup_active:
                if event.key == pygame.K_r:
                    reload_map(active_players, platforms, spawn_point, artifacts)
                    level_complete = False
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()

                if event.key == pygame.K_p:
                    time_paused = time.time()
                    paused = True

        if paused:
            action = await pause_menu(screen, level_name, window_size, time_paused)
            if action == False:
                paused = False
            elif action == "level restart":
                bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
                start_timer = pygame.time.get_ticks()
                popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in intro_popups + platform_popups]
                artifacts_collected = 0
                collected_artifacts = []
                increment_num = 1
                storm_activators = []
                for platform in platforms:
                    if platform.name == f"homeless-shelter{increment_num}":
                        if increment_num == 1:
                            introduceBunker = platform
                        storm_activators.append(platform)
                        increment_num += 1
                storm = Storm(trigger_distance=150, platforms=storm_activators, font=font, screen_size=(1000, 700))
                introduced_bunker = False
                paused = False
            elif action == "go to level select":
                running = False
            elif action == "go to home":
                return False
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
            action = await level_completed(screen, level_name, text_color, window_size, popup_text=post_mission_briefing, time_finished=time.time(), total_time=counting_string)
            if action == "level restart":
                bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
                start_timer = pygame.time.get_ticks()
                popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in intro_popups + platform_popups]
                artifacts_collected = 0
                collected_artifacts = []
                level_complete = False
                increment_num = 1
                storm_activators = []
                for platform in platforms:
                    if platform.name == f"homeless-shelter{increment_num}":
                        storm_activators.append(platform)
                        increment_num += 1
                storm = Storm(trigger_distance=150, platforms=storm_activators, font=font, screen_size=(1000, 700))
            elif action == "go to level select":
                running = False
            
            elif action == "go to home":
                return False
        
        else:
            while accumulator >= fixed_delta_time:
                update_game_logic(fixed_delta_time, active_players, platforms, keys, spawn_point, popup_active, ladders=ladders, hooks=hooks)
                for hook in hooks:
                    hook.update(fixed_delta_time)
                accumulator -= fixed_delta_time
                for player in active_players:
                    if player.id == 1:
                        camera.update(player, num_of_players)

            subscreens = getSplitscreenLayout(canvas, active_players)
            canvas.fill((0, 0, 0))
            renderSplitscreenLayout(canvas, active_players, num_of_players, bg_image, platforms, camera, death_platforms, artifacts, collected_artifacts, flashlight, volcanoes=None, ladders=ladders, hooks=hooks, subscreens=subscreens)
            counting_string = update_timer(start_timer)
            render_artifacts(artifacts, camera, collected_artifacts, surface=canvas)
            storm.draw(screen)
            render_artifact_count(("#56911f"), artifacts_collected)
            render_timer(lil_font, "#32854b", counting_string)


            for popup in popups:
                popup.update()

            for button in [RELOAD, PAUSE]:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)

            pygame.display.flip()

        await asyncio.sleep(0)

async def training(active_players):

    screen.fill("#020626")
    loading_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 40)
    loading_text = loading_font.render("loading...", True, ("#71d6f5"))
    loading_rect = loading_text.get_rect(center=(window_size[0] // 2, window_size[1] // 2))
    screen.blit(loading_text, loading_rect)
    pygame.display.update()
    
    from level_init import tutorialPlatformsInit

    level_name = 'Training'
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 60)
    lil_font = pygame.font.Font('fonts/pixelated.ttf', 35)
    text_color = ("#71d6f5")

    num_of_players = len(active_players)
    bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
    intro_to_jumping, intro_to_sliding, intro_to_jumpslide, artifacts = tutorialPlatformsInit(platforms, level_name)

    background_darkener = pygame.Surface((window_size[0], window_size[1]), pygame.SRCALPHA)
    background_darkener.fill((0, 0, 0, 129))

    for player in active_players:
        player.can_jump, player.can_slide = False, False
        introduced_controls_state["introduced_jumping"], introduced_controls_state["introduced_sliding"] = False, False
    
    intitial_popups = [

        {"name": "welcome",
        "screen": screen,
        "text": "Welcome to training!",
        "theme_color": text_color,
        "button_text": "Next",
        "visible": True
    },
    
        {"name": "purpose",
         "screen": screen,
         "text": "Here, you will learn the basics required to go out on missions",
         "theme_color": text_color,
         "button_text": "Next",
         "visible": False
    },

        {"name": "get_started",
         "screen": screen,
         "text": "To get started, walk forward",
         "theme_color": text_color,
         "button_text": "Got it",
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

            blit_jumpslide = player.on_platform == intro_to_jumpslide

            if player.position.y > level_height + 100:
                player.reload(spawn_point)

            if player.on_platform == finish_line:
                
                level_complete = True
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
                    reload_map(active_players, platforms, spawn_point, artifacts)
                    level_complete = False
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()

                if PAUSE.checkForInput(MENU_MOUSE_POS):
                    time_paused = time.time()
                    paused = True

            elif event.type == pygame.KEYDOWN and not popup_active:
                if event.key == pygame.K_r:
                    reload_map(active_players, platforms, spawn_point, artifacts)
                    level_complete = False
                    if spawn_point == OG_spawn_point or not next_checkpoints:
                        start_timer = pygame.time.get_ticks()

                if event.key == pygame.K_p:
                    time_paused = time.time()
                    paused = True

        if paused:
            action = await pause_menu(screen, level_name, window_size, time_paused)
            if action == False:
                paused = False
            elif action == "level restart":
                bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
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
            action = await level_completed(screen, level_name, text_color, window_size, popup_text="Hello. Nothing here, yet :)", time_finished=time.time(), total_time=counting_string)
            if action == "level restart":
                bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
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
                return False

        else:
            while accumulator >= fixed_delta_time:
                update_game_logic(fixed_delta_time, active_players, platforms, keys, spawn_point, popup_active, ladders=[], hooks=[])
                accumulator -= fixed_delta_time
            
            # Determine the layout dynamically based on the number of active players
            subscreens = getSplitscreenLayout(canvas, active_players)

            # Clear the canvas
            canvas.fill((0, 0, 0))  # Fill the canvas with black

            # Render game objects for each active player's view vow
            renderSplitscreenLayout(canvas, active_players, num_of_players, bg_image, platforms, camera, death_platforms, artifacts, collected_artifacts, flashlight, volcanoes=None, subscreens=subscreens, ladders=None, hooks=None)
            counting_string = update_timer(start_timer)
            render_artifact_count(("#56911f"), artifacts_collected)
            render_timer(lil_font, "#32854b", counting_string)
            display_controls(len(active_players), introduced_controls_state, print_player1_controls, print_player3_controls, print_player4_controls)
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
    lil_font = pygame.font.Font('fonts/pixelated.ttf', 30)
    lilest_font = pygame.font.Font('fonts/pixelated.ttf', 20)
    text_color = "#71d6f5"

    num_of_players = 1
    bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)

    show_settings = next((platform for platform in platforms if platform.name == 'settings'), None)
    show_level_select = next((platform for platform in platforms if platform.name == 'level-select'), None)

    artifact_image1 = pygame.image.load("Levels/Terus1/assets/artifact1.png")
    artifact_data = [
        {"image": artifact_image1, "position": (900, 1480), "name": "Golden Idol"},
        {"image": artifact_image1, "position": (500, 450), "name": "Ancient Vase"}
    ]

    game_info = [

        {
            "name": "intro1",
            "screen": screen,
            "text": "The biggest Nuclear Fusion reactor, powering over 50% of earth, is now meldown critical. We made a machine to fix the issue, but did not have essential materials.",
            "theme_color": text_color,
            "button_text": "And?",
            "visible": True
        },

        {
            "name": "intro2",
            "screen": screen,
            "text": "We sent out a ship of scientists called the Odyssey. The Odyssey has had an accident and has imploded. This is why we have called you here.",
            "theme_color": text_color,
            "button_text": "What do we do?",
            "visible": False
        },

        {
            "name": "intro3",
            "screen": screen,
            "text": "As a part of Project ASTRA, you must travel to the different planets in which the materials have landed and bring them back.",
            "theme_color": text_color,
            "button_text": "OK",
            "visible": False
        },

        {
            "name": "intro4",
            "screen": screen,
            "text": "Be aware that this mission is very dangerous, however, we have identified that you are the best candidate for this mission. You are to leave today. Godspeed.",
            "theme_color": text_color,
            "button_text": "Yes Sir!",
            "visible": False
        }
    ]

    popups = [Popup(data["name"], data["screen"], data["text"], data["theme_color"], data["button_text"], data["visible"]) for data in game_info]
    artifacts = pygame.sprite.Group(Artifact(data["image"], data["position"], data["name"]) for data in artifact_data)

    title_screen_text = mainTextInit(font, lil_font, text_color, window_size)
    level_select_text = lilest_font.render("Level select", True, text_color)

    running = True
    fixed_delta_time = 1 / 60
    accumulator = 0
    popup_index = 0
    previous_time = pygame.time.get_ticks()
    paused = False
    editing_settings = False
    reload_players = False
    blit_enter = False
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

        for popup in popups:
            if popup.visible:
                popup_active = True
                break
            else:
                popup_active = False

        if not popups[popup_index].visible and popup_index + 1 < len(game_info):
            popups[popup_index + 1].visible = True
            popup_index += 1

        for player in active_players:
            blit_enter = player.on_platform == show_level_select

            if player.position.y > level_height + 100:
                player.reload(OG_spawn_point)
                await training(active_players)

            if player.on_platform == show_settings and not editing_settings:
                if not reload_players:
                    time_entered_settings = time.time()
                    editing_settings = True
                else:
                    player.reload(spawn_point)
                    reload_players = False

            if player.on_platform == show_level_select:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_l or event.key == pygame.K_RETURN:
                            await levelSelect(active_players)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            for popup in popups:
                popup.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and not popup_active:
                if RELOAD.checkForInput(MENU_MOUSE_POS):
                    reload_map(active_players, platforms, spawn_point, artifacts)
                    text_color = "#71d6f5"

                if PAUSE.checkForInput(MENU_MOUSE_POS):
                    time_paused = time.time()
                    paused = True

            elif event.type == pygame.KEYDOWN and not popup_active:
                if event.key == pygame.K_l:
                    await levelSelect(active_players)

                if event.key == pygame.K_r:
                    reload_map(active_players, platforms, spawn_point, artifacts)
                    text_color = "#71d6f5"

                if event.key == pygame.K_p:
                    time_paused = time.time()
                    paused = True

        if paused:
            action = await pause_menu(screen, level_name, window_size, time_paused)
            if action == False:
                paused = False
            elif action == "level restart":
                bg_image, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, OG_spawn_point, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player3_controls, print_player4_controls, next_checkpoint = await load_level(level_name, num_of_players)
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
                update_game_logic(fixed_delta_time, active_players, platforms, keys, spawn_point, popup_active, ladders=[], hooks=[])
                accumulator -= fixed_delta_time

            screen.fill((0, 0, 0))
            screen.blit(bg_image, (0, 0))
            screen.blit(title_screen_text, (0, 0))
            render_game_objects(platforms, active_players, camera, flashlight, death_platforms=[], surface=screen)
            display_controls(len(active_players), introduced_controls_state, print_player1_controls, print_player3_controls, print_player4_controls)

            if blit_enter:
                screen.blit(pygame.image.load("assets/gameControls/keyboard_enter.png").convert_alpha(), (760, 647))
                screen.blit(level_select_text, (815, 670))

            for button in [RELOAD, PAUSE]:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)
            
            for popup in popups:
                popup.update()

            pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()

# # Run the main function
asyncio.run(main())

# Debugging and profiling code

# import pstats, cProfile

# with open(("Players/player_controls.json"), 'r') as key_map:
#     keys_data = json.load(key_map)

# player1_controls = keys_data['controls']['players']['player1']
# player2_controls = keys_data['controls']['players']['player2']
# player3_controls = keys_data['controls']['players']['player3']
# player4_controls = keys_data['controls']['players']['player4']

# players = {
#     "player1": Player(player_id=1, position=(64, 64), controls=player1_controls, color=("#9EBA01"))
#     }

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