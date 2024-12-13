import pygame
import asyncio
import json
import time
from PIL import Image, ImageFilter

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



"""player.py code goes here"""



class Player():


    def __init__(self, position, controls, color, player_id):
        super().__init__()
        self.id = player_id
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False
        self.on_platform = None
        self.under_platform = False
        self.jump_strength = 600
        self.speed = 200
        self.acceleration = 5000
        self.deceleration = 10000
        self.gravity = 50
        self.mass = 1
        self.facing = 0
        self.can_jump = True
        self.can_slide = True
        self.is_sliding = False
        self.slide_direction = 0
        self.slide_distance = 300
        self.controls = {action: getattr(pygame, key) for action, key in controls.items()}
        # self.animations = self.load_animations()
        # self.current_animation = self.animations["idle"]
        # self.shield = False
        # self.double_jump = False
        # self.effects = []
        # self.powerups = []

        "temp variables until we can add player sprites"

        self.width, self.height = 32, 64
        self.color = color
    
    def collisions(self, platforms):
        player_rect = self.rect
        self.on_ground = False
        tolerance = 10

        for platform in platforms:
            platform_rect = pygame.Rect(platform.position.x, platform.position.y, platform.dimensions[0], platform.dimensions[1])

            if player_rect.colliderect(platform_rect):
                overlap_x = min(player_rect.right - platform_rect.left, platform_rect.right - player_rect.left)
                overlap_y = min(player_rect.bottom - platform_rect.top, platform_rect.bottom - player_rect.top)

                if overlap_x < overlap_y:  # Horizontal collision
                    
                    if self.velocity.x > 0 and player_rect.left < platform_rect.left:  # Moving right into platform

                        self.position.x = platform_rect.left - self.width
                    
                    elif self.velocity.x < 0 and player_rect.right > platform_rect.right:  # Moving left into platform
                        self.position.x = platform_rect.right
                    
                    self.velocity.x = 0

                else:  # Vertical collision
                    
                    if self.velocity.y > 0:  # Falling
                        
                        self.position.y = platform_rect.top - self.height
                        self.velocity.y = 0
                        self.on_ground = True
                        self.on_platform = platform
                    
                    elif self.velocity.y < 0 and platform_rect.bottom - player_rect.top <= tolerance:  # Jumping
                        self.position.y = platform_rect.bottom + 3
                        self.velocity.y = 0

            player_rect = self.rect
  
    def load_animations(self):
        pass

    def update_animations(self):
        pass

    def momentum(self):
        return self.mass * self.velocity
    
    def jump(self):
        
        if self.on_ground:
            self.velocity.y = -self.jump_strength / self.mass
            self.on_ground = False

            if self.on_platform:
                self.on_platform = None

    def slide(self):
        if self.on_ground and not self.is_sliding:
            self.is_sliding - True
            self.start_slide = self.position.x
    

    def handle_controls(self, keys, delta_time, position):
        
        ACCELERATION = self.acceleration * delta_time
        DECELERATION = self.deceleration * delta_time

        if keys[self.controls['left']]:
            self.velocity.x -= ACCELERATION
            self.facing = -1

            if self.slide_direction == 1 and not self.under_platform:
                self.is_sliding = False
                
                self.width, self.height = 32, 64
                self.slide_direction = 0
        
        elif keys[self.controls['right']]:
            self.velocity.x += ACCELERATION
            self.facing = 1

            if self.slide_direction == -1 and not self.under_platform:
                self.is_sliding = False
                
                self.width, self.height = 32, 64
                self.slide_direction = 0
        else:
            
            if self.on_ground and not self.is_sliding:
                if self.velocity.x > 0:
                    self.velocity.x = max(0, self.velocity.x - DECELERATION)
                elif self.velocity.x < 0:
                    self.velocity.x = min(0, self.velocity.x + DECELERATION)

        MAX_SPEED = self.speed
        self.velocity.x = max(-MAX_SPEED, min(MAX_SPEED, self.velocity.x))

        if self.on_ground:

            if keys[self.controls['jump']] and self.can_jump:
                self.jump()
            
            if keys[self.controls['slide']] and not self.is_sliding and self.facing != 0 and self.can_slide:
                self.position.y += 32
                self.width, self.height = 64, 32
                self.start_slide = self.position.x
                self.is_sliding = True
                self.slide_direction = self.facing

        if self.is_sliding:
            distance_slid = abs(self.position.x - self.start_slide)

            if distance_slid < self.slide_distance:
                self.velocity.x = (self.slide_direction * self.speed) * 1.75

            elif self.on_ground and distance_slid > self.slide_distance:

                if not self.under_platform:
                    self.velocity.x = 0
                    self.is_sliding = False              
                    self.width, self.height = 32, 64

                if self.under_platform:
                    self.reload(position)
    
    def detect_headbumps(self, platforms):
        self.under_platform = False

        player_rect = self.rect

        head_zone = pygame.Rect(player_rect.x, player_rect.y - 64, player_rect.width, 32)

        for platform in platforms:
            platform_rect = pygame.Rect(
                platform.position.x, platform.position.y, platform.dimensions[0], platform.dimensions[1]
            )

            if head_zone.colliderect(platform_rect):
                self.under_platform = True
                break

    def update(self, delta_time, keys, platforms, position):
        
        self.gravity_and_motion(delta_time)
        self.handle_controls(keys, delta_time, position)
        self.detect_headbumps(platforms)

        if self.on_platform and self.on_platform.is_moving:
            self.position.x += self.on_platform.velocity.x * delta_time
        
        self.position += self.velocity * delta_time

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

    @property
    def rect(self):
        return pygame.Rect(self.position.x, self.position.y, self.width, self.height)

    def gravity_and_motion(self, delta_time):

        if not self.on_ground:
            self.velocity.y += self.gravity
            
        self.position.x += self.velocity.x * delta_time
        self.position.y += self.velocity.y * delta_time

    def reload(self, position):
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(0, 0)
        self.is_sliding = False
        self.facing = 0
        self.on_ground = False
        self.width, self.height = 32, 64



"""platform.py code goes here"""



class Platform():
    

    def __init__(self, name, position, is_moving, movement_range, speed, direction, image_path, dimensions, color):

        self.name = name
        self.position = pygame.Vector2(position)
        self.start_position = pygame.Vector2(position)
        self.is_moving = is_moving
        self.movement_range = pygame.Vector2(movement_range)
        self.speed = speed
        self.animation_frames = []
        self.current_frame = 0
        self.frame_count = len(self.animation_frames)
        self.direction = pygame.Vector2(direction)
        self.start_direction = self.direction.copy()
        self.previous_direction = self.direction.copy()
        self.image_path = image_path
        self.color = color
        self.dimensions = dimensions
        self.velocity = pygame.Vector2(0, 0)
        
        try:
            self.image = pygame.image.load(image_path).convert_alpha() if image_path else None
        except FileNotFoundError:
            self.image = None


    def update(self, dt):
        
        if self.is_moving == 'True':
            
            movement = pygame.Vector2(
                self.direction.x * self.movement_range.x,
                self.direction.y * self.movement_range.y
            ).normalize() * self.speed

            self.velocity = movement
            self.position += self.velocity * dt
            
            if self.position.distance_to(self.start_position) > self.movement_range.length() or self.position.x < self.start_position.x or self.position.y > self.start_position.y:
                self.direction *= -1
        
        if self.frame_count > 0:    
            self.current_frame = (self.current_frame + 1) % self.frame_count

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, self.position)
        else:
            pygame.draw.rect(screen, self.color, (*self.position, self.dimensions[0], self.dimensions[1]))
    
    def set_image(self, image_path):
        if image_path is not None:
            self.image = pygame.image.load(image_path)
        else:
            self.image = None

    
    def set_animation_frames(self, image_paths):
        self.animation_frames = [pygame.image.load(path) for path in image_paths]
        frame_count = len(self.animation_frames)

    def reset(self):
        self.position = pygame.Vector2(self.start_position)
        self.direction = pygame.Vector2(self.start_direction)
        self.current_frame = 0



"""camera.py goes here"""



class Camera():
    
    def __init__(self, width, height, window_size):
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.window_size = window_size
        self.zoom = 1
        self.margin = 100
        self.is_active = True

    def apply(self, obj):

        if self.is_active:

            if isinstance(obj, Player):
                rect = obj.rect.copy()
                rect.x = (rect.x - self.camera_rect.x) * self.zoom
                rect.y = (rect.y - self.camera_rect.y) * self.zoom
                rect.width *= self.zoom
                rect.height *= self.zoom
                return rect
            
            elif isinstance(obj, Platform):
                scaled_rect = pygame.Rect(
                    (obj.position.x - self.camera_rect.x) * self.zoom,
                    (obj.position.y - self.camera_rect.y) * self.zoom,
                    obj.dimensions[0] * self.zoom,
                    obj.dimensions[1] * self.zoom
                )
                return scaled_rect
        
        else:

            if isinstance(obj, Player):
                return obj.rect.move(-self.camera_rect.topleft[0], -self.camera_rect.topleft[1])
            
            elif isinstance(obj, Platform):
                return pygame.Rect(
                    obj.position.x - self.camera_rect.topleft[0],
                    obj.position.y - self.camera_rect.topleft[1],
                    obj.dimensions[0],
                    obj.dimensions[1]
                )
            
        return obj

    
    def update(self, players, player):
        
        if self.is_active:

            min_x = min(player.position.x for player in players)
            max_x = max(player.position.x for player in players)
            min_y = min(player.position.y for player in players)
            max_y = max(player.position.y for player in players)

            min_x -= self.margin
            max_x += self.margin
            min_y -= self.margin
            max_y += self.margin

            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2

            bounding_width = max_x - min_x
            bounding_height = max_y - min_y
            zoom_x = self.window_size[0] / bounding_width
            zoom_y = self.window_size[1] / bounding_height

            self.zoom = min(zoom_x, zoom_y, 1.0)

            camera_width = self.window_size[0] / self.zoom
            camera_height = self.window_size[1] / self.zoom
            self.camera_rect = pygame.Rect(
                max(0, min(center_x - camera_width / 2, self.width - camera_width)),
                max(0, min(center_y - camera_height / 2, self.height - camera_height)),
                camera_width,
                camera_height
            )
        
        if not self.is_active:
            
            x = player.position.x - 500
            y = player.position.y - (self.window_size[1] // 2)

            x = max(0, min(x, self.width - self.window_size[0]))
            y = max(0, min(y, self.height - self.window_size[0]))

            self.camera_rect = pygame.Rect(x, y, self.width, self.height)



"""buttons.py code goes here"""



class Button():

    def __init__(self, image, pos, font, base_color, hovering_color, text_input):
        self.image = image
        self.x_coordinate = pos[0]
        self.y_coordinate = pos[1]
        self.font = font
        self.base_color, self.hovering_color = base_color, hovering_color
        self.text_input = text_input
        self.text = self.font.render(self.text_input, True, self.base_color)

        if self.image is None:
            self.image = self.text
        
        elif self.text_input is None:
            self.text = self.image

        self.rect = self.image.get_rect(center=(self.x_coordinate, self.y_coordinate))
        self.text_rect = self.text.get_rect(center=(self.x_coordinate, self.y_coordinate))

    def update(self, screen):
        
        if self.image is not None:
            screen.blit(self.image, self.rect)
        
        screen.blit(self.text, self.text_rect)
    
    def checkForInput(self, position):

        if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
            return True
        return False
    
    def changeColor(self, position):

        if self.checkForInput(position):
            self.text = self.font.render(self.text_input, True, self.hovering_color)
        
        else:
            self.text = self.font.render(self.text_input, True, self.base_color)



"""parkour-dash.py code goes here"""



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

    EXIT_SETTINGS = Button(image=button_image, pos=(500, 500), text_input="exit", font=pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 20), base_color="#167fc9", hovering_color="#F59071")
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

async def main():

    level_name = 'home'
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
            
            elif level_name == 'home':

                if player.on_platform == show_settings and not editing_settings:

                    if not reload_players:

                        time_entered_settings = time.time()
                        editing_settings = True
                    
                    else:

                        player.reload(spawn_point)
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