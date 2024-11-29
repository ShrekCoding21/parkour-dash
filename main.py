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
        self.is_sliding = False
        self.slide_direction = 0
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

                        self.position.x = platform_rect.left - self.width - 5
                    
                    elif self.velocity.x < 0 and player_rect.right > platform_rect.right:  # Moving left into platform
                        self.position.x = platform_rect.right + 5
                    
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
                self.width, self.height = 32, 64
        
        elif keys[self.controls['right']]:
            self.velocity.x += ACCELERATION
            self.facing = 1

            if self.slide_direction == -1:
                self.is_sliding = False
                self.width, self.height = 32, 64
        else:
            
            if self.on_ground and not self.is_sliding:
                if self.velocity.x > 0:
                    self.velocity.x = max(0, self.velocity.x - DECELERATION)
                elif self.velocity.x < 0:
                    self.velocity.x = min(0, self.velocity.x + DECELERATION)

        MAX_SPEED = self.speed
        self.velocity.x = max(-MAX_SPEED, min(MAX_SPEED, self.velocity.x))

        if self.on_ground:

            if keys[self.controls['jump']]:
                self.jump()
            
            if keys[self.controls['slide']] and not self.is_sliding and self.facing != 0:
                self.start_slide = self.position.x
                self.is_sliding = True
                self.slide_direction = self.facing
                self.width, self.height = 64, 32

        if self.is_sliding:
            distance_slid = abs(self.position.x - self.start_slide)

            if distance_slid < 250:
                self.velocity.x = (self.slide_direction * self.speed) * 1.75

            else:

                self.width, self.height = 32, 64
                if self.on_ground:

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
    

    def __init__(self, position, is_moving, movement_range, speed, direction, image_path, dimensions, color):

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

class Camera():
    
    def __init__(self, width, height):
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, obj):

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
    
    def update(self, player):

        x = player.position.x - (self.width // 2) + 500
        y = player.position.y - self.height // 2

        x = max(0, min(x, self.width - window_size[0]))
        y = max(0, min(y, self.height - window_size[0]))

        self.camera_rect = pygame.Rect(x, y, self.width, self.height)

def load_platforms(platform_data, level_name):

    platforms = []
    level_data = platform_data[level_name]['platforms']

    for platform_name, platform_data in level_data.items():
        platform_dimensions = (platform_data['width'], platform_data['height'])
        platform_position = (platform_data['x-position'], platform_data['y-position'])
        platform_direction = (platform_data['x-direction'], platform_data['y-direction'])
        platform_movement_range = (platform_data['x-movement_range'], platform_data['y-movement_range'])

        platform = Platform(
            position=platform_position,
            is_moving = platform_data['is_moving'],
            image_path=platform_data['image_path'],
            dimensions=platform_dimensions,
            speed=platform_data['speed'],
            direction=platform_direction,
            movement_range=platform_movement_range,
            color = platform_data['color']
        )
            
        platforms.append(platform)

    return platforms

def freeze_game(screen, clock, window_size, paused, game_finished, best_player_num, text_color):

    if paused:
        text1 = "Paused"
        text2 = None
        f_size = 55

    if game_finished:
        text1 = f'player {best_player_num} wins!'
        text2 = 'press (r) to restart game'
        f_size = 35

    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', f_size)
    texts = [text1, text2]
    offset = 30

    for text in texts:        
        printtext = font.render(text, True, (text_color))
        text_rect = printtext.get_rect(center=(window_size[0] // 2, window_size[1] // 2 - offset))
        screen.blit(printtext, text_rect)
        offset = -offset

    pygame.display.flip()

    clock.tick(10)


def reload_players(players, platforms, reset_positions):
        
        for platform in platforms:
            platform.reset()

        for player, position in zip(players, reset_positions):
            player.reload(position)

def display_controls():
       
    font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 25)

    p1_controls = [
        'a: left',
        'd: right',
        'w: jump',
        's: slide'
        ]
    
    p2_controls = [
        'left-arrow: left',
        'right-arrow: right',
        'up-arrow: up',
        'down-arrow: slide'
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
            
def update_game_logic(delta_time, players, platforms, keys):

    for player in players:
        player.update(delta_time, keys)
        player.collisions(platforms)

    for platform in platforms:
        platform.update(delta_time)


async def main():

    keys_data = await load_json_file('Players/player_controls.json')
    levels_data = await load_json_file('Levels/demo_level.json')

    player1_controls = keys_data['controls']['players']['player1']
    player2_controls = keys_data['controls']['players']['player2']

    level_name = 'demo_level'
    level_type = levels_data[level_name]['level_type']
    platforms = load_platforms(levels_data, level_name)

    player1 = Player(player_id=1, position=(910, 610), controls=player1_controls, color=("#9EBA01"))
    player2 = Player(player_id=2, position=(910, 610), controls=player2_controls, color=("#2276c9"))

    players = [player1, player2]
    reset_positions = [(910, 610), (910, 610)]

    running = True
    fixed_delta_time = 1 / 60
    accumulator = 0
    paused = False
    finish_line = None
    game_finished = False
    best_player_num = None
    text_color = ("#71d6f5")

    for platform in platforms:
        if platform.position == pygame.Vector2(30, 100):
            finish_line = platform

    if level_type == 'scrolling':
        camera = Camera(width=2000, height=700)
    
    elif level_type == 'escape':
        camera = Camera(width=1000, height=700)

    while running:
        dt = clock.tick(60) / 1000.0
        accumulator += dt
        keys = pygame.key.get_pressed()

        for player in players:

            if player.position.y > 800:
                player.reload(position=(910, 610))

            if player.on_platform == finish_line:
                best_player_num = player.id
                game_finished = True
                text_color = player.color

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_r:
                    reload_players(players, platforms, reset_positions)
                    best_player_num = None
                    game_finished = False
                    text_color = ("#71d6f5")
                
                if event.key == pygame.K_p:
                    paused = True
                
                elif paused or game_finished:

                    if event.key == pygame.K_u:
                        paused = False
                    
                    elif event.key == pygame.K_r:
                        reload_players(players, platforms, reset_positions)
                        paused = False
                        game_finished = False
                        best_player_num = None
                        text_color = ("#71d6f5")

        if paused or game_finished:

            freeze_game(screen, clock, window_size, paused, game_finished, best_player_num, text_color)

        if not paused and not game_finished:

            while accumulator >= fixed_delta_time:
                update_game_logic(fixed_delta_time, players, platforms, keys)
                accumulator -= fixed_delta_time

                camera.update(player1)

            screen.fill((0, 0, 0))
            
            for platform in platforms:
                
                if platform.image:  # If the platform has an image
                    screen.blit(platform.image, camera.apply(platform))
                
                else:  # Fallback to solid color if no image
                    pygame.draw.rect(screen, platform.color, camera.apply(platform))

            for player in players:
                player_rect = camera.apply(player)
                pygame.draw.rect(screen, player.color, player_rect)

            display_controls()

            pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()

# Run the main function
asyncio.run(main())

"""if you read this you are nice"""