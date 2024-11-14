import pygame
import asyncio
import json
import os

WEB_ENVIRONMENT = False
try:
    import pygbag.fs # type: ignore
    WEB_ENVIRONMENT = True
except ImportError:
    pass  # We're not running in a web environment

pygame.init()
window_size = (800, 600)
screen = pygame.display.set_mode(window_size)
clock = pygame.time.Clock()

pygame.display.set_caption("Karthikeya Abhimanyu Ainapurapu")

async def load_json_file(filepath):
    if WEB_ENVIRONMENT:
        # Load file using pygbag.fs in a web environment
        with pygbag.fs.open(filepath, 'r') as key_map:
            keys_data = json.load(key_map)
    else:
        # Load file normally in a local environment
        with open(filepath, 'r') as key_map:
            keys_data = json.load(key_map)
    return keys_data

class Player():


    def __init__(self, player_name, position, controls, color):
        super().__init__()
        self.player_name = player_name
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False
        # self.is_sliding = False
        self.controls = {action: getattr(pygame, key) for action, key in controls.items()}
        # self.animations = self.load_animations()
        # self.current_animation = self.animations["idle"]
        # self.running_speed = 1
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
    
    def collisions(self):
        pass
    
    def load_animations(self):
        pass

    def update_animations(self):
        pass

    def jump(self):
        
        if self.on_ground:
            JUMP_STRENGTH = -10
            self.velocity.y = JUMP_STRENGTH
            self.on_ground = False

    def handle_controls(self, keys):

        if keys[self.controls['left']]:
            self.velocity.x = -25
        elif keys[self.controls['right']]:
            self.velocity.x = 25
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

        GRAVITY = 0.5
        if not self.on_ground:
            self.velocity.y += GRAVITY
        self.position.x += self.velocity.x * delta_time
        self.position.y += self.velocity.y * delta_time

class Platform():
    pass

class Powerups():
    pass

async def main():

    keys_data = await load_json_file('player_controls.json')

    player1_controls = keys_data['controls']['players']['player1']
    player2_controls = keys_data['controls']['players']['player2']

    player1 = Player(player_name="Player 1", position=(100, 100), controls=player1_controls, color=(0, 255, 0))
    player2 = Player(player_name="Player 2", position=(200, 100), controls=player2_controls, color=(0, 0, 255))

    running = True
    while running:
        delta_time = clock.tick(60) / 1000.0
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        player1.update(delta_time, keys)
        player2.update(delta_time, keys)

        screen.fill((0, 0, 0))
        player1.draw(screen)
        player2.draw(screen)
        pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()

# Run the main function
asyncio.run(main())
