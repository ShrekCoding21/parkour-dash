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

# Expected output (11/12)

Two green rectangles that can be controlled to go left and right using a and d or left arrow and right arrow while falling under force of gravity
Works either by running locally or by running on localhost:8000 dev server (server can be started using command, "pygbag main.py"; make sure to run "pip install pygbag" before trying test server)

# Features necessary for checkpoint 1

1) Left and right movement + jumping
2) Gravity and physics
3) Player hitboxes
4) Platforms
5) Scrolling demo level (not done)

# Extra features for checkpoint 1 (optional)

1) Player sprites and animations
2) Object sprites and animations
3) Powerups
4) Unique name creation
6) Title screen
7) Character appearance selection
8) Sliding button

# Next steps

1) Create scrolling level
2) Set up website to host video game

# *Player Class (11/19)*

# Names function (not used yet)

1) Defines player_names and player_ids as user defined variables
2) Allows users to input variables (input method will be changed in future)
3) Returns player_names and player_ids to let python identify the players and apply powerups and effects to them

# Collisions function

1) Initializes local variable from platforms class that returns platform position (bottom left corner) and dimensions; allows game to know where platforms are
2) Uses if statements to handle player collision with the platforms
    1) overlap_x & overlap_y: Defines how vertically & horizantally close the player & platforms are to eachother
    2) If player experiences horizontal collision with platform: player goes to either left or right of platform depending on direction of travel, if the platform collides with the player, then player moves to whichever side platform is traveling towards. Previous direction attribute prevents player from teleporting when platform switches direction
    3) If player experiences vertical collision with platform: if player is falling while on a platform, they are placed above platform to not clip through the platform and stay on top of it. If player is trying to jump while colliding with platform, if the distance between platform and player is less than 5 (they are very close to eachother), game lets player jump over platform, otherwise they collide with top of platform and fall back down.
    4) Player velocity is set to 0 after each statement so that player doesn't continue moving with the platform 
    


# *Useful resources*

karthik has a big forehead lololol
Complete python introduction course (very useful): https://www.youtube.com/playlist?list=PLeo1K3hjS3uv5U-Lmlnucd7gqF-3ehIh0
What is asyncio: https://youtu.be/Qb9s3UiMSTA?si=aUc02pHfXq4Ukhqs
How to come up with & create sprites (Adobe Photoshop): https://youtu.be/mBt3UuLJx9Y?si=M1b8WCtHLIM0PtI3
How to animate sprites (Adobe Photoshop): https://youtu.be/q2IxC0odOkU?si=dNo0REHtTp1Pw5KX
How to use sprite sheets in python: https://youtu.be/ePiMYe7JpJo?si=yzEy5BQZCaBM3CbN
How to deploy code to web (WebAssembly): https://youtu.be/q25i2CCNvis?si=PJp0aLba8GXqc6_v
General tips on coding: https://www.youtube.com/@CodeAesthetic



