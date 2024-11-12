# parkour-dash
TSA Video game design competition code for RLC.

# IMPORTANT - how to format this document

1) No useless information (about the code only)
2) The format should be as follows

# Title of new addition (date of addition)

1) Explain what additions you created here
2) Use new lines to make it easier to read changes

# Example future additions

1) Explain how you want to expand on your concept here

# ----- End formatting example -----

# Expected output (11/11)

Two green rectangles that can be controlled to go left and right using a and d or left arrow and right arrow while falling under force of gravity.

# Features necessary for checkpoint 1

1) Left and right movement + jumping
2) Gravity and physics
3) Player hitboxes
4) Platforms
5) Scrolling demo level

# Extra features for checkpoint 1 (optional)

1) Player sprites and animations
2) Object sprites and animations
3) Powerups
4) Unique name creation
5) Pause button
6) Title screen
7) Character appearance selection
8) Sliding button
9) Platforms

# Next steps

1) Add demo platform (11/12 - 11/16)
2) Set up website to host video game
3) Add powerups (after rest of checkpoint 1 submission is ready)

# *player_controls.JSON* (11/11)

1) Stores information for keys to be used by players

# Future updates (player_controls.json)

1) Include any new keys to be used by players in the game

# *parkour_dash.py*

# Names function (11/11)

1) Gets player names & stores in list (player_names)
2) Creates player id for each player and stores in list (player_ids)
3) Uses basic validation with if statements to ensure name isn't empty and <21 characters

# Future updates (names function)

1) Will contain way for players to choose a skin as well
2) Messages will be different probably

# Collisions function (not implemented yet; 11/11)

1) Handles player collisions with platforms
2) Handles player collisions with enemies
3) Handles player collisions with powerups

# Load_animations function (not implemented yet; 11/12)

1) Maps each spritesheet to an name (Ex: Idle, running, jumping)
2) Returns names for rest of program to utilize

# Update_animations function (not implemented yet; 11/12)

1) Consistently runs checks on the player
2) Runs animations based on current player actions

# Jump function (11/11)

1) Tells program what the player does when it jumps
2) Tells program when player can and is jumping (when on ground and pressing jump key)

# Future updates (jump function)

1) Tell code to run jump animation (when it exists)

# Handle_controls function (11/11)

1) Uses key map from player_controls.JSON
2) Defines what player should do if certain keys are pressed (for left, right, and jump)

# Future updates (handle_controls function)

1) Define what sliding does and when it should be done

# Gravity_and_motion function (11/11)

1) Initializes gravitational constant (0.5 for now)
2) Tells program when to apply gravity (when not on ground)
3) Defines where player position should be based on velocity and elapsed time

# Future updates (gravity_and_motion function)

1) Change gravitational constant in the future based on preferences

# Update function (11/11)

1) Ensures program is continuously responding to keypresses (by running handle_controls function)
2) Ensures program continuously runs physics calculations (by running gravity_and_motion function)

# Future updates (update function)

1) Ensure program continuously responds to collisions (using future collisions function)

# Draw function (11/11)

1) Creates rectangle (demo player) based on position and dimension variables defined in player instance and init function respectively

# Future updates (draw function)

1) Draw an animated sprite (character) rather than placeholder rectangle
2) Use screen.blit function to reduce code in main game loop

# Rect function (11/11)

1) Defines properties of player (hitbox size and position)
