import pygame
import asyncio
import json

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
    

    def handle_controls(self, keys, delta_time):
        
        ACCELERATION = self.acceleration * delta_time
        DECELERATION = self.deceleration * delta_time

        if keys[self.controls['left']]:
            self.velocity.x -= ACCELERATION
            self.facing = -1

            if self.slide_direction == 1:
                self.is_sliding = False
                
                if self.on_ground:
                    self.position.y -= 32
                
                self.width, self.height = 32, 64
                self.slide_direction = 0
        
        elif keys[self.controls['right']]:
            self.velocity.x += ACCELERATION
            self.facing = 1

            if self.slide_direction == -1:
                self.is_sliding = False
                
                if self.on_ground:
                    self.position.y -= 32
                
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

                self.width, self.height = 32, 64
                self.position.y -= 32
                self.is_sliding = False
                self.velocity.x = 0
                

            

    def update(self, delta_time, keys):
        
        self.gravity_and_motion(delta_time)
        self.handle_controls(keys, delta_time)

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
        self.zoom = 1.0
        self.margin = 100
        self.is_active = True

    def apply(self, obj):

        if self.is_active:

            if isinstance(obj, Player):
                rect = obj.rect.copy()
                rect.x = (rect.x - self.camera_rect.x) * self.zoom
                rect.y = (rect.y - self.camera_rect.y) * self.zoom
                rect.width *= self.zoom
                rect.height00 *= self.zoom
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



"""parkour-dash.py code goes here"""



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


def reload_map(players, platforms, reset_positions):
        
        for platform in platforms:
            platform.reset()

        for player, position in zip(players, reset_positions):
            player.reload(position)

def display_controls(introduced_controls_state, counting_string, timer_color):
    
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 25)

    if not introduced_controls_state["introduced_jumping"]:
        
        p1_controls = [
            'a: left',
            'd: right'
        ]

        p2_controls = [
            '←: left',
            '→: right'
        ]

        p3_controls = [
            'g: left',
            'j: right'
        ]

        p4_controls = [
            'k: left',
            'semicolon: right'
        ]
    
    elif not introduced_controls_state["introduced_sliding"] and introduced_controls_state["introduced_jumping"]:

        p1_controls = [
            'a: left',
            'd: right',
            'w: jump'
        ]

        p2_controls = [
            '←: left',
            '→: right',
            '↑: jump'
        ]

        p3_controls = [
            'g: left',
            'j: right',
            'y: jump',
        ]

        p4_controls = [
            'k: left',
            'semicolon: right',
            'o: jump'
        ]
        

    else:

        p1_controls = [
            'a: left',
            'd: right',
            'w: jump',
            's: slide'
            ]
        
        p2_controls = [
            '←: left',
            '→: right',
            '↑: up',
            '↓: slide'
            ]
        
        p3_controls = [
            'g: left',
            'j: right',
            'y: jump',
            'h: slide'
        ]

        p4_controls = [
            'k: left',
            'semicolon: right',
            'o: jump',
            'l: slide'
        ]
        
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

    for p3_control in p3_controls:
        print_p3_controls = font.render(p3_control, True, ("#c7b61a"))
        p3_control_rect = print_p3_controls.get_rect(topright=(x_position, vertical_displacement))
        screen.blit(print_p3_controls, p3_control_rect)
        vertical_displacement += 30

    for p4_control in p4_controls:
        print_p4_controls = font.render(p4_control, True, ("#c7281a"))
        p4_control_rect = print_p4_controls.get_rect(topright=(x_position, vertical_displacement))
        screen.blit(print_p4_controls, p4_control_rect)
        vertical_displacement += 30
            
def update_game_logic(delta_time, players, platforms, keys):

    for player in players:
        player.update(delta_time, keys)
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

def render_game_objects(platforms, players, camera):

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

    for player in players:

        player_rect = camera.apply(player)
        scaled_rect = pygame.Rect(
            player_rect.x,
            player_rect.y,
            int(player_rect.width),
            int(player_rect.height)
        )
        pygame.draw.rect(screen, player.color, scaled_rect)

def update_tutorial_controls(players, introduce_jumping, introduce_sliding, introduced_controls_state):
    """Allow players to use new controls when reaching new section and tell display_controls function to display new controls"""

    for player in players:
        
        if player.on_platform == introduce_jumping and not introduced_controls_state["introduced_jumping"]:
            introduced_controls_state["introduced_jumping"] = True

        elif player.on_platform == introduce_sliding and not introduced_controls_state["introduced_sliding"]:
            introduced_controls_state["introduced_sliding"] = True

    if introduced_controls_state["introduced_jumping"]:
        for player in players:
            player.can_jump = True

    if introduced_controls_state["introduced_sliding"]:
        for player in players:
            player.can_slide = True


async def main():

    keys_data = await load_json_file('Players/player_controls.json')
    
    level_name = 'tutorial_level'  # Select either tutorial_level or demo_level

    levels_data = await load_json_file(f'Levels/{level_name}.json')

    player1_controls = keys_data['controls']['players']['player1']
    player2_controls = keys_data['controls']['players']['player2']
    player3_controls = keys_data['controls']['players']['player3']
    player4_controls = keys_data['controls']['players']['player4']

    level_type = levels_data[level_name]['level_type']
    platforms = load_platforms(levels_data, level_name)

    OG_spawn_point, introduce_jumping, introduce_sliding, death_platforms, next_checkpoints, finish_line = get_special_platforms(platforms, level_name)


    player1 = Player(player_id=1, position=OG_spawn_point, controls=player1_controls, color=("#9EBA01"))
    player2 = Player(player_id=2, position=OG_spawn_point, controls=player2_controls, color=("#2276c9"))
    player3 = Player(player_id=3, position=OG_spawn_point, controls=player3_controls, color=("#c7b61a"))
    player4 = Player(player_id=4, position=OG_spawn_point, controls=player4_controls, color=("#c7281a"))

    players = [player1, player2, player3, player4]
    spawn_point = OG_spawn_point
    checkpoint_increment = 0
    reset_positions = []

    for player in players:
        reset_positions.append(spawn_point)
    
    if level_type == 'scrolling':
        next_checkpoint = next_checkpoints[checkpoint_increment]
        level_width, level_height = levels_data[level_name]['camera_width'], levels_data[level_name]['camera_height']
        camera = Camera(width=level_width, height=level_height, window_size=window_size)
        camera.is_active = True # CHANGE LATER
        introduced_controls_state = {"introduced_jumping": False, "introduced_sliding": False}
        
        for player in players:
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
            update_tutorial_controls(players, introduce_jumping, introduce_sliding, introduced_controls_state)

        for player in players:

            if player.position.y > level_height + 100:
                player.reload(spawn_point)

            if player.id == 4:
                print(player.position)

            if player.on_platform == finish_line:
                reset_positions = []
                best_player_num = player.id
                game_finished = True
                text_color = player.color
                checkpoint_increment = 0
                spawn_point = OG_spawn_point

                for player in players:
                    reset_positions.append(spawn_point)

                for platform in next_checkpoints:
                    platform.color = "#9ff084"
                
                if level_type == 'scrolling':
                    spawn_point = OG_spawn_point
                    reset_positions = []
                    next_checkpoint = next_checkpoints[checkpoint_increment]
                    introduced_controls_state = {"introduced_jumping": False, "introduced_sliding": False}
                    
                    for player in players:
                        reset_positions.append(spawn_point)
                        player.can_jump, player.can_slide = False, False    

            if level_type == 'scrolling':

                if player.on_platform in death_platforms:
                    player.reload(spawn_point)

                if player.on_platform == next_checkpoint:
                    spawn_point = (next_checkpoint.position.x + (next_checkpoint.dimensions[0] / 2), next_checkpoint.start_position.y - next_checkpoint.dimensions[1])
                    next_checkpoint.color = "#228700"
                    reset_positions = []
                    
                    for player in players:

                        reset_positions.append(spawn_point)
                    
                    if checkpoint_increment < len(next_checkpoints) - 1:
                        checkpoint_increment += 1
                        next_checkpoint = next_checkpoints[checkpoint_increment]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_r:
                    reload_map(players, platforms, reset_positions)  
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
                        reload_map(players, platforms, reset_positions)
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
                update_game_logic(fixed_delta_time, players, platforms, keys)
                accumulator -= fixed_delta_time
                camera.update(players, player)

            screen.fill((0, 0, 0))
            
            counting_string = update_timer(start_timer)
            render_game_objects(platforms, players, camera)
            display_controls(introduced_controls_state, counting_string, timer_color=("#32854b"))

            pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()

# Run the main function
asyncio.run(main())

"""if you read this you are nice"""