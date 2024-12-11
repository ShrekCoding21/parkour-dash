import pygame
import asyncio
import time
from Players.player import Player
from camera import Camera
from Buttons.buttons import Button
from game_init import load_json_file, load_platforms, pause_menu, level_complete, introduce_controls, reload_map, display_controls, determine_blitted_controls, update_game_logic, update_timer, get_special_platforms, render_game_objects, update_tutorial_controls

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

async def main():

    keys_data = await load_json_file('Players/player_controls.json')
    
    level_name = 'home'  # Select tutorial_level, demo_level, or home

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

    OG_spawn_point, introduce_jumping, introduce_sliding, introduce_jumpsliding, death_platforms, next_checkpoints, finish_line = get_special_platforms(platforms, level_name)

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

    running = True
    fixed_delta_time = 1 / 60
    accumulator = 0
    start_timer = pygame.time.get_ticks()
    paused = False
    game_finished = False
    best_player_num = None
    text_color = ("#71d6f5")
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
                    level_name == 'tutorial_level'
                    

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

                for platform in next_checkpoints:
                    platform.color = "#9ff084"
                
                if level_name == 'tutorial_level':
                    next_checkpoint = next_checkpoints[checkpoint_increment]
                    introduced_controls_state["introduced_jumping"], introduced_controls_state['introduced_sliding'] = False, False
                    
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



        elif game_finished:

            level_complete(screen, clock, window_size, counting_string, best_player_num, text_color)

        else:

            while accumulator >= fixed_delta_time:
                update_game_logic(fixed_delta_time, active_players, platforms, keys, position=spawn_point)
                accumulator -= fixed_delta_time
                camera.update(active_players, player)

            screen.fill((0, 0, 0))
            
            counting_string = update_timer(start_timer)
            render_game_objects(platforms, active_players, camera)
            display_controls(introduced_controls_state, counting_string, print_player1_controls, print_player2_controls, print_player3_controls, print_player4_controls, p2_active, p3_active, p4_active, timer_color=("#32854b"))
            introduce_controls(blit_jumpslide)

            for button in [RELOAD, PAUSE]:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)

            pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()

# Run the main function
asyncio.run(main())

"""if you read this you are nice"""