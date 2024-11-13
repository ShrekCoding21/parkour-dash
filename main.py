import pygame
import asyncio
import json
import os

# Check if we're running in the web environment
WEB_ENVIRONMENT = False
try:
    import pygbag.fs # type: ignore
    WEB_ENVIRONMENT = True
except ImportError:
    pass  # We're not running in a web environment

# Initialize Pygame and set up the window
pygame.init()
window_size = (800, 600)
screen = pygame.display.set_mode(window_size)
clock = pygame.time.Clock()

pygame.display.set_caption("Karthikeya Abhimanyu Ainapurapu")

# Function to load JSON data, supports both local and web environments
async def load_json_file(filepath):
    if WEB_ENVIRONMENT:
        # Load file using pygbag.fs in a web environment
        with pygbag.fs.open(filepath, 'r') as key_map:
            data = json.load(key_map)
    else:
        # Load file normally in a local environment
        with open(filepath, 'r') as key_map:
            data = json.load(key_map)
    return data

class Player():
    """Defines attributes of each of the 2 players in the game"""

    def __init__(self, player_name, position, controls): # initializes the class
        super().__init__()
        self.player_name = player_name # defines which player is which using name function (since there are 2 players)
        self.position = pygame.Vector2(position) # defines where the player spawns in (position variable is a tuple)
        self.velocity = pygame.Vector2(0, 0) # defines starting velocity as none
        self.on_ground = False # tells python whether player is on ground or not
        # self.is_sliding = False # tells code whether player is sliding or not
        self.controls = {action: getattr(pygame, key) for action, key in controls.items()} # tells code what keys the player can use depending on whether player 1 or 2
        # self.animations = self.load_animations() # calls load_animations function to load beginning animations
        # self.current_animation = self.animations["idle"] # tells animations function to load idle animation for players
        # self.running_speed = 1 # sets starting running speed (before powerups are applied)
        # self.shield = False # sets player to initially not have shield buff
        # self.double_jump = False # sets player to not initially be able to double jump
        # self.effects = [] # Empty list of effects applied to character (effects will be appended automatically)
        # self.powerups = [] # Empty list of powerups applied to player (useful for applying animations and stuff)

        "temp variables until we can add player sprites"

        self.width = 32
        self.height = 64
        self.color = (0, 255, 0)

    def names(self):
        """Allows user to choose their name (used to identify player)"""

        player_names = [] # stores names of both players to be accessed by program
        player_ids = [] # stores player ids ("player" + i) for key mapping
        for i in range(2): # runs code 2 times to get both player's names
            player_num = i + 1
            invalid = True

            while invalid: # only lets player continue if their name is valid
                player_name = input(f"Player {player_num}, please enter your name") # method of getting names may have to change later

                if player_name != '' and len(player_name) < 21:
                    if player_name not in player_names:
                        player_ids.append(f'player{player_num}')
                        player_names.append(player_name) # adds entered valid name to list of player names
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
        "Tells program how to handle jumping"
        if self.on_ground:
            JUMP_STRENGTH = -10
            self.velocity.y = JUMP_STRENGTH
            self.on_ground = False

    def handle_controls(self, keys):
        "Tells program how to handle different buttons using key map from player_controls.JSON"
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
    # Load JSON control data asynchronously
    keys_data = await load_json_file('player_controls.json')

    player1_controls = keys_data['controls']['players']['player1']
    player2_controls = keys_data['controls']['players']['player2']

    player1 = Player(player_name="Player 1", position=(100, 100), controls=player1_controls)
    player2 = Player(player_name="Player 2", position=(200, 100), controls=player2_controls)

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
