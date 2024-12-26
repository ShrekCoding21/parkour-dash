import pygame

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
    

    def handle_controls(self, keys, delta_time, position, popup_active):
        
        if popup_active:
            return
        
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

    def update(self, delta_time, keys, platforms, position, popup_active):
        
        self.gravity_and_motion(delta_time)
        self.handle_controls(keys, delta_time, position, popup_active)
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