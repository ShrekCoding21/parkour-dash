import pygame

class Platform():
    

    def __init__(self, position, image, is_moving, movement_range, speed, direction, image_path, dimensions, color):

        self.start_position = pygame.Vector2(position)
        self.position = pygame.Vector2(position)
        self.is_moving = is_moving
        self.movement_range = pygame.Vector2(movement_range)
        self.speed = speed
        self.animation_frames = []
        self.current_frame = 0
        self.frame_count = len(self.animation_frames)
        self.direction = pygame.Vector2(direction)
        self.image_path = image_path
        self.image = image
        self.color = color
        self.dimensions = dimensions

    def update(self, dt):
        if self.is_moving:
            self.position += self.direction * self.speed * dt
            if self.position.distance_to(self.start_position) > self.movement_range.length():
                self.direction *= -1
        if self.frame_count > 0:    
            self.current_frame = (self.current_frame + 1) % self.frame_count

    def draw(self, screen):
        if self.animation_frames:
            frame = self.animation_frames[self.current_frame]
            screen.blit(frame, self.position)
        else:
            if self.is_moving:
                pygame.draw.rect(screen, self.color, (*self.position, self.dimensions[0], self.dimensions[1]))
    
    def set_image(self, image_path):
        if image_path is not None:
            image = pygame.image.load(image_path)
            self.animation_frames = [image]
            self.frame_count = len(self.animation_frames)
        else:
            self.animation_frames = []
            self.frame_count = 0

    
    def set_animation_frames(self, image_paths):
        self.animation_frames = [pygame.image.load(path) for path in image_paths]
        frame_count = len(self.animation_frames)

    def reset(self):
        self.position = pygame.Vector2(self.start_position)
        self.current_frame = 0
