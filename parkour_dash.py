import pygame
import asyncio
import time
from Buttons.buttons import Button
from assets.sprites import Spritesheet
from game_init import load_cutscene, settings_menu, load_level, pause_menu, level_complete, introduce_controls, reload_map, display_controls, update_game_logic, update_timer, render_game_objects, update_tutorial_controls

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

async def main():

    await load_cutscene(canvas)

    level_name = 'home'
    bg_image = pygame.image.load("assets/parkour_dash_background.png").convert_alpha()
    bg_image = pygame.transform.scale(bg_image, window_size)
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 60)
    lil_font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 25)
    text_color = ("#71d6f5")

    print_welcome1 = font.render("welcome to", True, (text_color))
    print_welcome2 = font.render("project AstRA", True, (text_color))
    show_tutorial_level1 = lil_font.render("jump here for tutorial", True, (text_color))
    show_tutorial_level2 = lil_font.render("↓", True, (text_color))
    show_settings1 = lil_font.render("← settings", True, (text_color))
    highlight_game_controls1 = lil_font.render("these could be useful→", True, (text_color))

    print_welcome1_rect = print_welcome1.get_rect(center=(500, 155))
    print_welcome2_rect = print_welcome2.get_rect(center=(500, 230))
    show_tutorial_level1_rect = show_tutorial_level1.get_rect(center=(600, 525))
    show_tutorial_level2_rect = show_tutorial_level2.get_rect(center=(550, 550))
    show_settings1_rect = show_settings1.get_rect(center=(125, 475))
    highlight_game_controls1_rect = highlight_game_controls1.get_rect(center=(435, 50))

    num_of_players = 1
    show_settings, checkpoint_increment, reset_positions, spawn_point, platforms, camera, active_players, introduced_controls_state, level_height, introduce_jumping, introduce_sliding, OG_spawn_point, introduce_jumpsliding, death_platforms, next_checkpoints, finish_line, print_player1_controls, print_player2_controls, print_player3_controls, print_player4_controls, p2_active, p3_active, p4_active, next_checkpoint = await load_level(level_name, num_of_players)   

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
                    level_name = 'tutorial_level'
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

            for button in [RELOAD, PAUSE]:
                button.changeColor(pygame.mouse.get_pos())
                button.update(screen)

            pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()

# Run the main function
asyncio.run(main())

"""if you read this you are nice"""