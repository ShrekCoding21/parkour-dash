import pygame

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