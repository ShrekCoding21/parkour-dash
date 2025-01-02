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