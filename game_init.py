import pygame
from Platforms.platform import Platform
from artifacts import Artifact

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

def centerText(text, position):
    """
    Centers given text on the screen

    Args:
        text (pygame.Surface): Text to center
        position (tuple): Position to center text at
    """
    return text.get_rect(center=position)

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

    print(platforms)
    return platforms

def introduce_controls(blit_jumpslide):

    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 30)

    print_jumpslide_tutorial1 = font.render("press jump and slide keys", True, ("#00f7f7"))
    print_jumpslide_tutorial2 = font.render("together to leap", True, ("#00f7f7"))
    jumpslide_tutorial_rect1 = print_jumpslide_tutorial1.get_rect(center=(500, 180))
    jumpslide_tutorial_rect2 = print_jumpslide_tutorial2.get_rect(center=(500, 220))
    
    if blit_jumpslide:
        screen.blit(print_jumpslide_tutorial1, jumpslide_tutorial_rect1)
        screen.blit(print_jumpslide_tutorial2, jumpslide_tutorial_rect2)

def reload_map(active_players, platforms, reset_position, artifacts):

    for platform in platforms:
        platform.reset()

    for player in active_players:
        player.reload(reset_position)

    for artifact in artifacts:
        artifact.reset()

def display_controls(num_of_players, introduced_controls_state, print_player1_controls, print_player3_controls, print_player4_controls):
    """
    Displays the control instructions for players on the game screen.
    Parameters:
    num_of_players (int): The number of players in the game.
    show_controls (bool): Flag to determine whether to show the controls on the screen.
    introduced_controls_state (dict): A dictionary indicating which controls have been introduced.
        Keys include "introduced_jumping" and "introduced_sliding".
    print_player1_controls (list): List of control instructions for player 1.
    print_player3_controls (list): List of control instructions for player 3.
    print_player4_controls (list): List of control instructions for player 4.
    Returns:
    None
    """
    
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 25)
    
    full_p1_controls = print_player1_controls
    full_p2_controls = [
            '←: left',
            '→: right',
            '↑: jump',
            '↓: slide'
        ]
    full_p3_controls = print_player3_controls
    full_p4_controls = print_player4_controls

    p1_controls = []
    p2_controls = []
    p3_controls = []
    p4_controls = []

    if not introduced_controls_state["introduced_jumping"]:
        p1_controls = [full_p1_controls[0], full_p1_controls[1]]

        if num_of_players > 1:
            p2_controls = [full_p2_controls[0], full_p2_controls[1]]
        if num_of_players > 2:
            p3_controls = [full_p3_controls[0], full_p3_controls[1]]
        if num_of_players > 3:
            p4_controls = [full_p4_controls[0], full_p4_controls[1]]


    
    elif not introduced_controls_state["introduced_sliding"] and introduced_controls_state["introduced_jumping"]:

        p1_controls = [full_p1_controls[0], full_p1_controls[1], full_p1_controls[2]]
        
        if num_of_players > 1:
            p2_controls = [full_p2_controls[0], full_p2_controls[1], full_p2_controls[2]]

        if num_of_players > 2:
            p3_controls = [full_p3_controls[0], full_p3_controls[1], full_p3_controls[2]]

        if num_of_players > 3:
            p4_controls = [full_p4_controls[0], full_p4_controls[1], full_p4_controls[2]]        
        
    else:

        p1_controls = full_p1_controls       
        
        if num_of_players > 1:
            p2_controls = full_p2_controls
        
        if num_of_players > 2:       
            p3_controls = full_p3_controls
        
        if num_of_players > 3:
            p4_controls = full_p4_controls
    
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

    if num_of_players > 1:

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

    vertical_displacement = 450

    if num_of_players > 2:

        for p3_control in p3_controls:
            print_p3_controls = font.render(p3_control, True, ("#c7b61a"))
            p3_control_rect = print_p3_controls.get_rect(topright=(x_position, vertical_displacement))
            screen.blit(print_p3_controls, p3_control_rect)
            vertical_displacement += 30

    if num_of_players > 3:

        for p4_control in p4_controls:
            print_p4_controls = font.render(p4_control, True, ("#c7281a"))
            p4_control_rect = print_p4_controls.get_rect(topright=(x_position, vertical_displacement))
            screen.blit(print_p4_controls, p4_control_rect)
            vertical_displacement += 30

def determine_blitted_controls(p1_controls, p3_controls, p4_controls):

    print_player1_controls = []
    print_player3_controls = []
    print_player4_controls = []

    for action, key in p1_controls.items():
        print_player1_controls.append(f'{action}: {key}')

    for action, key in p3_controls.items():
        print_player3_controls.append(f'{action}: {key}')

    for action, key in p4_controls.items():
            print_player4_controls.append(f'{action}: {key}')

    return print_player1_controls, print_player3_controls, print_player4_controls
            
def update_game_logic(delta_time, active_players, platforms, keys, position, popup_active, ladders, hooks):

    for player in active_players:
        player.update(delta_time, keys, platforms, position, popup_active, ladders, hooks)
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

def render_timer(font, text_color, counting_string):
    print_timer = font.render(counting_string, True, text_color)
    timer_rect = print_timer.get_rect(topright=(990, 100))
    screen.blit(print_timer, timer_rect)

def get_special_platforms(platforms, level_name):

    next_checkpoints = list()
    deathforms = list()
    checkpoint_num = 1
    deathpoint_num = 1

    for platform in platforms:

        if platform.name == "starting-platform":
            spawn_point = (platform.position.x + (platform.dimensions[0] / 2), platform.position.y - platform.dimensions[1])

        elif platform.name == f"checkpoint{checkpoint_num}":
            print(platform)
            next_checkpoints.append(platform)
            checkpoint_num += 1

        elif platform.name == "finish-line":
            finish_line = platform

        elif platform.name == f"death-form{deathpoint_num}":
            deathforms.append(platform)
            deathpoint_num += 1

    return spawn_point, deathforms, next_checkpoints, finish_line

def is_flashlight_touching_platform(flashlight_beam, platform_rect, flashlight):
    """
    Checks for collision between the flashlight beam and a platform.

    Args:
        flashlight_beam: The rotated surface of the flashlight beam.
        platform_rect: The pygame.Rect object representing the platform's position.
        flashlight: Flashlight object (if applicable).

    Returns:
        True if the beam collides with the platform, False otherwise.
    """

    # Get the rectangle of the beam surface
    beam_rect = flashlight_beam.get_rect()

    # Calculate the center of the beam rectangle based on the flashlight's position
    beam_center_x = flashlight.pos.x - beam_rect.width // 2
    beam_center_y = flashlight.pos.y - beam_rect.height // 2
    beam_rect.center = (beam_center_x, beam_center_y)

    # Check for collision between the beam rectangle and platform rectangle
    return beam_rect.colliderect(platform_rect)

def renderSplitscreenLayout(canvas, active_players, num_of_players, bg_image, platforms, camera, death_platforms, artifacts, collected_artifacts, flashlight, volcanoes, ladders, hooks, subscreens):
    for i, sub in enumerate(subscreens):
        if i < len(active_players):
            player = active_players[i]
            camera.update(player, num_of_players)
            bg_image_scaled = pygame.transform.scale(bg_image, sub.get_size())
            sub.blit(bg_image_scaled, (0, 0))
            if volcanoes != None:
                for volcano in volcanoes:
                    volcano.update()
                    volcano.draw(camera, sub)
            if ladders != None:
                for ladder in ladders:
                    ladder.draw(camera, sub)
            if hooks != None:
                for hook in hooks:
                    hook.draw(camera, sub)
            render_game_objects(platforms, active_players, camera, flashlight, death_platforms, surface=sub)
            render_artifacts(artifacts, camera, collected_artifacts, surface=sub)

            # Draw dividing lines to separate the views
    if len(active_players) == 2:
        pygame.draw.line(canvas, (255, 255, 255), (window_size[0] // 2, 0), (window_size[0] // 2, window_size[1]), 5)
    elif len(active_players) == 3:
                # Three players: Draw two horizontal lines to divide into thirds
        pygame.draw.line(canvas, (255, 255, 255), (0, window_size[1] // 3), (window_size[0], window_size[1] // 3), 5)
        pygame.draw.line(canvas, (255, 255, 255), (0, (2 * window_size[1]) // 3), (window_size[0], (2 * window_size[1]) // 3), 5)
    elif len(active_players) == 4:
        pygame.draw.line(canvas, (255, 255, 255), (window_size[0] // 2, 0), (window_size[0] // 2, window_size[1]), 5)
        pygame.draw.line(canvas, (255, 255, 255), (0, window_size[1] // 2), (window_size[0], window_size[1] // 2), 5)

            # Blit the subsurfaces to the main screen
    for i, sub in enumerate(subscreens):
        if len(active_players) == 1:
            screen.blit(sub, (0, 0))
        elif len(active_players) == 2:
            x = (i % 2) * (window_size[0] // 2)
            y = 0
            screen.blit(sub, (x, y))
        elif len(active_players) == 3:
            x = 0 
            y = (i % 3) * (window_size[1] // 3)
            screen.blit(sub, (x, y))
        elif len(active_players) == 4:
            x = (i % 2) * (window_size[0] // 2)
            y = (i // 2) * (window_size[1] // 2)
            screen.blit(sub, (x, y))

def getSplitscreenLayout(canvas, active_players):
    if len(active_players) == 1:
        p1_camera = pygame.Rect(0, 0, window_size[0], window_size[1])
        subscreens = [canvas.subsurface(p1_camera)]
    elif len(active_players) == 2:
        p1_camera = pygame.Rect(0, 0, window_size[0] // 2, window_size[1])
        p2_camera = pygame.Rect(window_size[0] // 2, 0, window_size[0] // 2, window_size[1])
        subscreens = [canvas.subsurface(p1_camera), canvas.subsurface(p2_camera)]
    elif len(active_players) == 3:
        p1_camera = pygame.Rect(0, 0, window_size[0], window_size[1] // 3)
        p2_camera = pygame.Rect(0, window_size[1] // 3, window_size[0], window_size[1] // 3)
        p3_camera = pygame.Rect(0, (2 * window_size[1]) // 3, window_size[0], window_size[1] // 3)
        subscreens = [canvas.subsurface(p1_camera), canvas.subsurface(p2_camera), canvas.subsurface(p3_camera)]
    else:
        p1_camera = pygame.Rect(0, 0, window_size[0] // 2, window_size[1] // 2)
        p2_camera = pygame.Rect(window_size[0] // 2, 0, window_size[0] // 2, window_size[1] // 2)
        p3_camera = pygame.Rect(0, window_size[1] // 2, window_size[0] // 2, window_size[1] // 2)
        p4_camera = pygame.Rect(window_size[0] // 2, window_size[1] // 2, window_size[0] // 2, window_size[1] // 2)
        subscreens = [
                    canvas.subsurface(p1_camera),
                    canvas.subsurface(p2_camera),
                    canvas.subsurface(p3_camera),
                    canvas.subsurface(p4_camera),
                ]
        
    return subscreens

def render_game_objects(platforms, active_players, camera, flashlight, death_platforms, surface):
    """
    Renders game objects on a specific surface, respecting camera and flashlight settings.
    """
    # If the flashlight is on, draw the beam first relative to the subscreen
    if flashlight.on:
        flashlight_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        flashlight.draw(camera, flashlight_surface)
        surface.blit(flashlight_surface, (0, 0))

    for platform in platforms:
        platform_rect = camera.apply(platform)

        # Create a temporary surface for platform rendering
        platform_surface = pygame.Surface((platform_rect.width, platform_rect.height), pygame.SRCALPHA)
        platform_surface.fill((0, 0, 0, 0))  # Transparent initially

        if hasattr(platform, 'image') and platform.image:
            platform_surface.blit(platform.image, (0, 0))
        else:
            if platform in death_platforms:
                platform_color = (0, 0, 0, 0)  # Transparent for death platforms
            else:
                if flashlight.enabled:
                    platform_color = (0, 0, 0)  # Black if flashlight is on
                else:
                    platform_color = platform.color  # Default platform color

            # Draw the platform color if no image is rendered
            if platform_color:
                pygame.draw.rect(platform_surface, platform_color, (0, 0, platform_rect.width, platform_rect.height))

            # Perform flashlight intersection calculations only if the flashlight is on
            if flashlight.on:
                is_hit = is_flashlight_touching_platform(flashlight.rotated_beam, platform_rect, flashlight)

                if is_hit:
                    # Create masks for the flashlight beam and platform
                    mask = pygame.mask.from_surface(flashlight.rotated_beam)
                    platform_mask = pygame.mask.from_surface(platform_surface)

                    # Get the intersection of the masks
                    intersection = mask.to_surface()

                    # Apply a darker blending to the platform surface
                    darkened_color = (255 * 0.5, 255 * 0.5, 255 * 0.5)  # Darker version of the platform color
                    platform_surface.blit(intersection, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    platform_surface.fill(darkened_color, special_flags=pygame.BLEND_RGBA_MULT)

        # Draw the platform on the provided surface
        surface.blit(platform_surface, platform_rect)

    # Render players
    for player in active_players:
        player_rect = camera.apply(player)
        scaled_rect = pygame.Rect(
            player_rect.x,
            player_rect.y,
            int(player_rect.width),
            int(player_rect.height)
        )
        pygame.draw.rect(surface, player.color, scaled_rect)

def getArtifacts(platforms, level_name):
    artifact_platform_num = 1
    artifact_platforms = []

    # Identify platforms that should have artifacts
    for platform in platforms:
        if platform.name == f"artifact-platform{artifact_platform_num}":
            artifact_platforms.append(platform)
            artifact_platform_num += 1

    # Artifact image
    artifact_image1 = pygame.image.load(f"Levels/{level_name}/assets/artifact1.png")

    # Create Artifact objects and add them to a sprite group
    artifacts = pygame.sprite.Group()
    for i, platform in enumerate(artifact_platforms):
        artifact_name = f"Artifact {i + 1}"  # Generate a unique name
        artifact_position = (
            platform.position.x + platform.dimensions[0] // 2 - 50,
            platform.position.y - 100
        )
        artifacts.add(Artifact(artifact_image1, artifact_position, artifact_name))
    return artifacts

def render_artifacts(artifacts, camera, collected_artifacts, surface):
    """
    Renders artifacts for a given level

    Args:
        artifacts (dict): List of all artifacts in the level to be rendered
        camera (Camera object): Current level camera so camera movement is properly applied to artifacts
        collected_artifacts (list): List of artifacts that have already been collected so they are not rendered again
        surface (pygame.Surface): Surface to blit the artifacts on
    """

    for artifact in artifacts:
        if artifact not in collected_artifacts and not artifact.collected:
            artifact_rect = camera.apply(artifact)  # Apply camera transformation
            artifact_scaled_rect = pygame.Rect(
                artifact_rect.x,
                artifact_rect.y,
                int(artifact_rect.width * camera.zoom),
                int(artifact_rect.height * camera.zoom)
            )
            surface.blit(artifact.image, artifact_scaled_rect.center)  # Draw artifact image at top-left of scaled rect

def render_artifact_count(text_color, artifacts_collected, font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 20)):
    print_artifacts_collected = font.render(f"artifact fragments collected: {artifacts_collected}", True, text_color)
    artifact_counter_rect = print_artifacts_collected.get_rect(center=(window_size[0] // 2 - 20, 20))
    screen.blit(print_artifacts_collected, artifact_counter_rect)

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