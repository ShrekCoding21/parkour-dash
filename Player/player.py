import pygame

class Player():


    def __init__(self, player_name, position, controls, color):
        super().__init__()
        self.player_name = player_name
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False
        self.jump_strength = 750
        self.speed = 150
        self.gravity = 50
        # self.is_sliding = False
        self.controls = {action: getattr(pygame, key) for action, key in controls.items()}
        # self.animations = self.load_animations()
        # self.current_animation = self.animations["idle"]
        # self.shield = False
        # self.double_jump = False
        # self.effects = []
        # self.powerups = []

        "temp variables until we can add player sprites"

        self.width = 32
        self.height = 64
        self.color = color

    def names(self):

        player_names = []
        player_ids = []
        for id_num in range(2): 
            player_num = id_num + 1
            invalid = True

            while invalid:
                player_name = input(f"Player {player_num}, please enter your name")

                if player_name != '' and len(player_name) < 21:
                    if player_name not in player_names:
                        player_ids.append(f'player{player_num}')
                        player_names.append(player_name)
                        invalid = False
                    else:
                        print("That name is already being used, please choose a different one.")
                else:
                    print("Invalid name. Please choose a name smaller than 21 characters and not blank.")
      
        return player_names, player_ids
    
    def collisions(self, platforms):
        player_rect = self.rect
        self.on_ground = False

        for platform in platforms:
            platform_rect = pygame.Rect(platform.position.x, platform.position.y, platform.width, platform.height)

            if player_rect.colliderect(platform_rect):

                if self.velocity.y > 0:
                    self.position.y = platform_rect.top - self.height
                    self.velocity.y = 0
                    self.on_ground = True
                elif self.velocity.y < 0:
                    self.position.y = platform_rect.bottom
                    self.velocity.y = 0

                player_rect = self.rect

        for platform in platforms:
                platform_rect = pygame.Rect(platform.position.x, platform.position.y, platform.width, platform.height)
                
                if player_rect.colliderect(platform_rect):

                    if self.velocity.x > 0:
                        self.position.x = platform_rect.left - self.width
                    elif self.velocity.x < 0:
                        self.position.x = platform_rect.right

                    player_rect = self.rect
    
    def load_animations(self):
        pass

    def update_animations(self):
        pass

    def jump(self):
        
        if self.on_ground:
            JUMP_STRENGTH = -self.jump_strength
            self.velocity.y = JUMP_STRENGTH
            self.on_ground = False

    def handle_controls(self, keys):
        
        if keys[self.controls['left']]:
            self.velocity.x = -self.speed
        elif keys[self.controls['right']]:
            self.velocity.x = self.speed
        else:
            self.velocity.x = 0

        if keys[self.controls['jump']] and self.on_ground:
            self.jump()

    def update(self, delta_time, keys):

        self.gravity_and_motion(delta_time)
        self.handle_controls(keys)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

    @property
    def rect(self):
        return pygame.Rect(self.position.x, self.position.y, self.width, self.height)

    def gravity_and_motion(self, delta_time):

        GRAVITY = self.gravity
        if not self.on_ground:
            self.velocity.y += GRAVITY
        self.position.x += self.velocity.x * delta_time
        self.position.y += self.velocity.y * delta_time
