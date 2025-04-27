# parkour-dash
TSA Video game design competition code for RLC.

# IMPORTANT - read the following rules and adhere to them

1) No useless information (about the code only)
2) Include helpful information such as how to use your changes (ex: what inputs are in a function), the date of the change, and what you plan on doing to expand on it (so that other people can help)
3) DON'T PUSH CHANGES THAT DON'T WORK TO THE REPOSITORY

# Game Documentation and tutorials

1) How to create levels
2) How to create custom platform behavior

*How to create levels*

1) Important warnings when making platforms/levels
2) How to create and setup json file (basic)
3) How to add images and movement to platforms
4) Where are these files read?
5) How to open level in main.py

*IMPORTANT INFORMATION - PLEASE READ IF NEW TO THIS*

1) Certain platform names are reserved to those with certain behaviors
    - starting-platform (REQUIRED): Player will spawn in the center of this platform at beginning of level
    - checkpoint{num} (REQUIRED): If player lands on this platform, it will turn dark green meaning player has reached a checkpoint
    - finish-line (REQUIRED for now): Level will be completed if player lands on this platform
    - death-form{num} (not required): If player lands on this platform, they respawn at last checkpoint or starting-platform (not supported in levels other than tutorial level yet)
    - artifact-platform{num} (not required): Tells game to load artifact on those platforms (if you run getArtifacts)

2) If you would like to add custom behaviors to these platforms, then please do so in the python file that was created for each platform. This is the code ran at level initialization, so more custom behaviors can be baesd off of this (located in level_init.py).
 
![image](https://github.com/user-attachments/assets/e7f63945-6c23-4f44-8024-241736217825)

3) If you are confused, Sreekar will probably be happy to help



*Step 1 - Creating json file*

1) Create a json key for your platform (go to useful resources if you don't understand)
2) Add proper structuring to your json file (especially if it is scrolling level)
  - Define properties of general level (before defining your platforms)
    - level_type: Scrolling or escape (escape defaults to a level size of 700x1000 (so no camera movement), scrolling requires an extra variable)
    - camera_dimensions (if level is scrolling level): Tuple containing width and height of full level so camera knows how far it needs to focus

Example of json file setup for each level (replace tutorial_level with the name of your json file; i.e. Terus1.json --> Terus1)

![image](https://github.com/user-attachments/assets/798adc0c-95c5-40e4-adce-4e3df168cd93)

3) Define basic properties for each platform
    - x-position: What x-coordinate is your platform located at
    - y-position: What y-coordinate is your platform located at (Going down INCREASES y-value; idk why)
    - width: How wide do you want your platform to be (going to the right from defined x-position)
    - height: How tall do you want your platform to be (going down from defined y-position)
    - is_moving: Boolean value of true or false depending on if platform should move or not (explained in step 2)
    - color: Hexadecimal/HTML notation value for color of platform
4) Example of a basic properly defined platform

![image](https://github.com/user-attachments/assets/878f5a57-505d-427f-ba01-bf4d6a3eef81)

*Step 2 - Adding images and movement to platforms (optional)*

To add custom properties to the platform, you simply have to add new parameters, and python will properly interpret them

1) For movement
    - is_moving: Set to true
    - speed: Integer value for how fast platform should go (pixels/second)
    - x-direction: Integer value of either 1 or -1 (1 means platform goes right first, -1 means platform goes left first)
    - y-direction: Integer value of either 1 or -1 (1 means platform goes up first, -1 means platform goes down first)
    - x-movement-range: How far left or right should platform move from starting point defined in step 1?
    - y-movement-range: How far up or down should platform move from starting point defined in step 1?

Example of properly defined moving platform (with no image)

![image](https://github.com/user-attachments/assets/216d5d78-d99b-4a21-8d5c-ae640aca5928)

2) For custom images
    - image_path: File path (relative to project scope) to platform image (preferably should be kept somewhere in platforms folder for       organization)

Example of properly defined platform with image

![image](https://github.com/user-attachments/assets/f43ebf35-eccb-480e-aa1a-99fd6e082e00)

*Step 3 - Opening and testing your level in main.py*

If you want to test your level, you can add an if statement in the for event in events loop in main.py and set it so if you press a
certain keyboard key it opens your level's function and runs it. Make sure that when you create your level function, when the player presses the home button in the pause menu, it simply stops running your loop, since this automatically takes the player to the home page.

![image](https://github.com/user-attachments/assets/eee6ea8c-678e-4c66-ad48-4659810fdfbb)

*How to create custom platform behavior*

Either use the platforms from the important info section or create your own based off of the structure

Example: Making a platform that prints something when u are on it

1) Define the platform using a function in the level_init.py file

![image](https://github.com/user-attachments/assets/8a32515e-21dd-4a9d-97d3-fedd8d236d3a)

2) Import that function in your level initialization

![image](https://github.com/user-attachments/assets/88908e97-43a1-4992-8896-c69693b456cd)

3) Setup the text that you want to print as well as the surface you want it to be printed on

![image](https://github.com/user-attachments/assets/6c76f54a-c9e3-4eb8-b5b4-28f3613f0c2b)

4) Define a boolean variable that is true if player is on platform, false if they are not (in game loop)

![image](https://github.com/user-attachments/assets/3e2d4275-6738-46a8-b191-129a6bfca411)

5) Define logic to blit the text on the screen if the boolean variable is true (alongside player rendering and stuff)

![image](https://github.com/user-attachments/assets/04c41b75-8892-4511-a171-e318412c4fdd)

# *Useful resources*

i have a big forehead lololol
1) Complete python introduction course (very useful): https://www.youtube.com/playlist?list=PLeo1K3hjS3uv5U-Lmlnucd7gqF-3ehIh0
2) What is asyncio: https://youtu.be/Qb9s3UiMSTA?si=aUc02pHfXq4Ukhqs
3) How to come up with & create sprites (Adobe Photoshop): https://youtu.be/mBt3UuLJx9Y?si=M1b8WCtHLIM0PtI3
4) How to animate sprites (Adobe Photoshop): https://youtu.be/q2IxC0odOkU?si=dNo0REHtTp1Pw5KX
5) How to use sprite sheets in python: https://youtu.be/ePiMYe7JpJo?si=yzEy5BQZCaBM3CbN
6) How to deploy code to web (WebAssembly): https://youtu.be/q25i2CCNvis?si=PJp0aLba8GXqc6_v
7) General tips on coding: https://www.youtube.com/@CodeAesthetic



