import pygame
from game_init import getArtifacts

"""Unlike the game init function, which manages game wide logic, this file is meant to be for storing level-specific logic, such
as handling custom platforms and other behaviors that don't exist in other levels. This is meant to save space in main.py so that
its easier to focus on the most critical game logic. Like the game_init file, this file should only store synchronous functions, and
any async functions should stay in main.py."""

def terusPlatformsInit(platforms, level_name):
    platform_dict = {platform.name: platform for platform in platforms}
    show_slide = platform_dict.get("show-slide")
    show_slide2 = platform_dict.get("jump-platform4")
    show_checkpoint1_reached = platform_dict.get("checkpoint1")
    show_checkpoint2_reached = platform_dict.get("checkpoint2")
    brighten_scene = platform_dict.get("main-artifact-platform")
    artifacts = getArtifacts(platforms, level_name)
    return show_slide, show_slide2, show_checkpoint1_reached, show_checkpoint2_reached, brighten_scene, artifacts

def scopulosusPlatformsInit(level_name, platforms):
    platform_dict = {platform.name: platform for platform in platforms}
    introduce_volcano = platform_dict.get("introduce-volcano")
    introduce_deathcano = platform_dict.get("jump-platform4")
    one_way = platform_dict.get("checkpoint3")
    artifacts = getArtifacts(platforms, level_name)
    return introduce_volcano,introduce_deathcano,one_way,artifacts

def tutorialPlatformsInit(platforms, level_name):
    platform_dict = {platform.name: platform for platform in platforms}
    intro_to_jumping = platform_dict.get("introduce-jumping")
    intro_to_sliding = platform_dict.get("introduce-sliding")
    intro_to_jumpslide = platform_dict.get("introduce-jumpsliding")
    artifacts = getArtifacts(platforms, level_name)
    return intro_to_jumping, intro_to_sliding, intro_to_jumpslide, artifacts

def mainTextInit(font, lil_font, text_color, window_size):
    # Create a surface to hold all the text and background elements
    text_group_surface = pygame.Surface((window_size[0], window_size[1]), pygame.SRCALPHA)
    
    # Fill the surface with a transparent darkened background (optional)
    background_darkener = pygame.Surface((window_size[0], window_size[1]), pygame.SRCALPHA)
    background_darkener.fill((0, 0, 0, 129))
    text_group_surface.blit(background_darkener, (0, 0))

    # Render text
    print_welcome1 = font.render("welcome to", True, text_color)
    print_welcome2 = font.render("project AstRA", True, text_color)
    show_tutorial_level1 = lil_font.render("jump here for tutorial", True, text_color)
    show_tutorial_level2 = lil_font.render("↓", True, text_color)
    show_settings1 = lil_font.render("← settings", True, text_color)
    highlight_game_controls1 = lil_font.render("these could be useful→", True, text_color)

    # Define positions
    text_group_surface.blit(print_welcome1, print_welcome1.get_rect(center=(500, 155)))
    text_group_surface.blit(print_welcome2, print_welcome2.get_rect(center=(500, 230)))
    text_group_surface.blit(show_tutorial_level1, show_tutorial_level1.get_rect(center=(530, 525)))
    text_group_surface.blit(show_tutorial_level2, show_tutorial_level2.get_rect(center=(500, 550)))
    text_group_surface.blit(show_settings1, show_settings1.get_rect(center=(125, 475)))
    text_group_surface.blit(highlight_game_controls1, highlight_game_controls1.get_rect(center=(435, 50)))

    return text_group_surface