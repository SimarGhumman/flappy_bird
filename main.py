##!/usr/bin/env python
'''
    @author [mst]
    @file   main.py
    @brief  <title or quick description>
    pygame learning using pygame
    based on: https://youtu.be/UZg49z76cLw
    this uses pygame. install with: pip install pygame

    log:
    -2022.02.25 asynced and packed with pygbag
                -issues running in browser: FAILED
                attempted to run with a pyinstaller exe: FAILED
    -2021.01.10 games mechanics, high scores and reset
    -2021.01.02 random pipes generation
    -2020.12.25 canvas, blips, rectangles
    -2020.12.07 init
    -[wip] ooptimize


    @version 0.1 2023.02
'''

import asyncio
import pygame           # main game lib
from sys import exit    # system utils (exit)
import random           # variable elements positioning and textures
# import ssl          # packaging async
# import http.client
# import json

# def post_score(score):
#     context = ssl._create_unverified_context()
#     conn = http.client.HTTPSConnection("drmfxb7c5f63d.cloudfront.net", context=context)
#     payload = json.dumps({
#         "id": "Simar",
#         "score": score
#     })
#     headers = {
#         'Content-Type': 'application/json'
#     }
#     conn.request("POST", "/post_score", payload, headers)
#     response = conn.getresponse()
#     data = response.read()
#     print("Post Score Response:", data.decode("utf-8"))
#     conn.close()
    
# constants
# [bp] use caps for const values
DISPLAY_WIDTH  = 576
DISPLAY_HEIGHT = 1024
FPS = 120   # frames per second
FONT_SIZE = 50
FONT_ANTIALIAS = False
SOUND_FREQ = 44100
SOUND_SIZE = -16
SOUND_CHANNELS = 2
SOUND_BUFFER = 512
COLOR_RGB = [255, 255, 255]
SCORE_X = DISPLAY_WIDTH/2
SCORE_Y = 100
HIGHSCORE_Y = 900
MAX_NAME_LENGTH = 8

FLOOR_HEIGHT = 950
FLOOR_SPEED = 1
GRAVITY_COEFF = 0.25    # gravity acceleration
BIRD_START_X = 100
BIRD_START_Y = DISPLAY_HEIGHT/2
BIRD_START_SPEED = -10
BIRD_ROTATION_COEFF = 3 # bird surface rotation sensitivity
BIRD_FLAP_POWER = 7     # how strong is the bird's flap. decrease to make game easier :)
BIRD_FLAP_FREQ = 300    #flapping animation speed
BIRD_DISPLAY_TOLERANCE = 100
PIPE_START_X = DISPLAY_WIDTH + 200
PIPE_HEIGHTS = [400, 600, 800]  # possible pipes heights variations
PIPE_MARGIN = 300   # the clearance between the pipes
PIPE_SPEED = 5
PIPE_FREQ = 1200    # pipes spawning frequency (in ms)

SPAWNPIPE_EVT = pygame.USEREVENT    # custom event to spawn a pipe
BIRD_FLAP_EVT = pygame.USEREVENT+1  # custom event to spawn a pipe

############
# game mechanics related variables
#
gravity = GRAVITY_COEFF
bird_speed = BIRD_START_SPEED
game_active = False # indicate a un-halted game
game_score = 0
high_score = 0  # [wip] load from a saved value
player_name = ''
input_active = False
high_score = 0  # Initial high score
high_score_name = "Test"  # Initial name for the high score
# to make a continuous floor, we make two floor surfaces move alternately
def draw_floor():
    screen.blit(floor_surface, (floor_x,FLOOR_HEIGHT))
    screen.blit(floor_surface, (floor_x+DISPLAY_WIDTH,FLOOR_HEIGHT))

# different bird animation surfaces are loaded as a list
# and are changed via a user timer event
def bird_animation():
    global bird_flap_index, bird_surface, bird_rect
    bird_flap_index = (bird_flap_index + 1) % len(bird_flaps)
    bird_surface = bird_flaps[bird_flap_index]
    new_bird_rect = bird_surface.get_rect(center=(BIRD_START_X, bird_rect.centery))
    bird_rect = new_bird_rect
    return bird_surface, bird_rect

# surfaces rotation will lower its quality so we rotate and create a new surface each time
# [wip] make a lambda function for this
def rotate_bird(bird_surface):
    global bird_speed

    rotation_angle = -bird_speed * BIRD_ROTATION_COEFF # we will let the bird speed determine the rotation angle
    new_surface = pygame.transform.rotozoom(bird_surface,rotation_angle,1)
    return new_surface

def draw_bird(bird_rotated):
    screen.blit(bird_rotated, bird_rect)


def move_pipes(pipe_rect_list_a):
    for pipe_rect in pipe_rect_list_a:
        pipe_rect.centerx -= PIPE_SPEED
    return pipe_rect_list_a

def draw_pipes(pipe_rect_list_a):
    global pipe_surface # [wip] parametrize this correctly
    for pipe_rect in pipe_rect_list_a:
        if pipe_rect.top < 0:   # flip the upper pipe texture, spot it by rect boundary
            pipe_surface_l = pygame.transform.flip(pipe_surface, False, True)
        else:
            pipe_surface_l = pipe_surface
        screen.blit(pipe_surface_l, pipe_rect)

def create_pipe():
    global pipe_surface
    pipe_height = random.choice(PIPE_HEIGHTS)
    pipe_surface = random.choice(pipe_surfaces) # [wip] this changes all pipes texture, make individual
    bottom_pipe = pipe_surface.get_rect(midtop = (PIPE_START_X, pipe_height)) # place by midtop
    upper_pipe = pipe_surface.get_rect(midbottom = (PIPE_START_X, pipe_height - PIPE_MARGIN)) # place at midbottom
    return bottom_pipe, upper_pipe  # the two pipes are returned as a tuple

# Check collisions and manage high score comparison
def check_collisions(pipe_rect_list_a):
    global input_active, game_score, high_score
    if bird_rect.top <= -BIRD_DISPLAY_TOLERANCE or bird_rect.bottom >= FLOOR_HEIGHT:
        die_sound.play()
        if game_score > high_score:
            input_active = True  # Enable name input only if new high score is achieved
        else:
            input_active = False  # Disable input if not a high score
        return False

    for pipe in pipe_rect_list_a:
        if bird_rect.colliderect(pipe):
            collision_sound.play()
            return False
    return True


# render score as text and draw as a surface
# [wip] single score printing function, parametrized by game state
def draw_score():
    score_surface = game_font.render(str(game_score), FONT_ANTIALIAS, COLOR_RGB)
    score_rect = score_surface.get_rect(center = (SCORE_X, SCORE_Y))
    screen.blit(score_surface, score_rect)  # [demo] origin of the surfaces is the top left

def draw_highscore():
    highscore_text = f'High Score: {high_score_name} {int(high_score)}'
    highscore_surface = game_font.render(highscore_text, FONT_ANTIALIAS, COLOR_RGB)
    highscore_rect = highscore_surface.get_rect(center=(SCORE_X, HIGHSCORE_Y))
    screen.blit(highscore_surface, highscore_rect)

# renewing the game
def reset_game():
    global bird_speed    # reset bird movement
    bird_speed = BIRD_START_SPEED

    global game_score   # reset the running score
    game_score = 0

    bird_rect.center = (BIRD_START_X, BIRD_START_Y)
    pipe_rect_list.clear()  # clear all the pipes at start of game

    global game_active
    game_active = True  # re-launch the game

def update_highscore():
    global game_score, high_score, high_score_name, player_name
    if game_score > high_score:
        high_score = game_score
        high_score_name = player_name  # Update name with new high score
        
    # global game_score, high_score
    
    # context = ssl._create_unverified_context()
    # conn = http.client.HTTPSConnection("drmfxb7c5f63d.cloudfront.net", context=context)
    # conn.request("GET", "/get_scores")
    # response = conn.getresponse()
    # data = response.read().decode('utf-8')
    # leaderboard = json.loads(data)

    # if leaderboard['scores']:
    #     highest_score = max(leaderboard['scores'], key=lambda x: x['score'])
    #     high_score = highest_score['score']

    # # Check if the current game score is a new high score
    # if game_score > high_score:
    #     high_score = game_score
    #     post_score(game_score)
    #     if game_score > high_score:
    #         print("New high score achieved and posted successfully!")
    #     else:
    #         print("Score matched and posted successfully!")

# user exits game functionality:
def exit_app():
    pygame.quit()
    exit()  # terminating the game engine is not enough. we must also quit the app itself


############
# pygame related variables

# pre-initializing audio engine sampling for optimization
pygame.mixer.pre_init(SOUND_FREQ, SOUND_SIZE, SOUND_CHANNELS, SOUND_BUFFER)

 # [demo] the game engine works as follows:
# init (+define a screen) -> paint a canvas -> main game loop (logic, user input, screen update) -> quit
#
pygame.init()

# create a screen (canvas)
screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))

# set a clock for frame rate control
clock = pygame.time.Clock()

# [demo] working with text is:
# set font -> render text -> create a surface -> put on screen
game_font = pygame.font.Font('assets/04B_19.TTF', FONT_SIZE)




############
# importing assets
# [demo] we can have many surfaces that can be displayed on a single display surface
# [demo] we use.convert() to convert an image to a more efficient format
# [demo] we use convert_alpha() to avoid black pixels during rotation/animation
# [demo] for better collision control, we will use rect to engulf the graphics in geometric shapes
# [demo] drawing on a screen goes as follows:
# import an asset as surface -> scale/transform -> overlay with rect if needed -> put/blip on screen

# background image and the floor as a surfaces. we double the size for the given screen
bg_surface = pygame.transform.scale2x(pygame.image.load('assets/background-day.png').convert())
floor_surface = pygame.transform.scale2x(pygame.image.load('assets/base.png').convert())
floor_x = 0

# the bird surface
# we will use timer-based flapping animation with different surfaces
bird_flaps = [pygame.transform.scale2x(pygame.image.load('assets/bluebird-downflap.png').convert_alpha()),
              pygame.transform.scale2x(pygame.image.load('assets/bluebird-midflap.png').convert_alpha()),
              pygame.transform.scale2x(pygame.image.load('assets/bluebird-upflap.png').convert_alpha())]
bird_flap_index = 0
bird_surface =  bird_flaps[bird_flap_index]
bird_rect = bird_surface.get_rect(center = (BIRD_START_X, BIRD_START_Y))  # this will draw a rectangle around the bird surface
pygame.time.set_timer(BIRD_FLAP_EVT, BIRD_FLAP_FREQ)

# the pipes surface
# we will use a list of pipe rects to be populated and drawn at a defined frequency
# [wip] fix all pipes in the list changing colors at once
pipe_surfaces = [pygame.transform.scale2x(pygame.image.load('assets/pipe-red.png').convert()),
                pygame.transform.scale2x(pygame.image.load('assets/pipe-green.png').convert())]
pipe_rect_list = []
pygame.time.set_timer(SPAWNPIPE_EVT, PIPE_FREQ) # here we define a timer within the game engine

# greeting/game over surface
greeting_surface = pygame.transform.scale2x(pygame.image.load('assets/message.png').convert_alpha())
greeting_rect = greeting_surface.get_rect(center = (DISPLAY_WIDTH/2, DISPLAY_HEIGHT/2))

flap_sound = pygame.mixer.Sound('sound/sfx_wing.wav')
game_score_sound = pygame.mixer.Sound('sound/sfx_point.wav')
die_sound = pygame.mixer.Sound('sound/sfx_die.wav')
collision_sound = pygame.mixer.Sound('sound/sfx_hit.wav')
swooshing_sound = pygame.mixer.Sound('sound/sfx_swooshing.wav')

def action():
    global bird_speed
    global game_active
    if game_active:
        bird_speed = 0   # halt gravity effect upon a flap
        bird_speed -= BIRD_FLAP_POWER
        flap_sound.play()
    else:
        reset_game()

async def main():
    global game_active
    global pipe_rect_list
    global floor_x
    global bird_speed
    global game_score
    global gravity
    global bird_rect
    global input_active
    global player_name
    
    ############
    # main game loop
    #
    # [wip] change to: while not game_end
    while True:
         ############
        # watch for events throughout the main loop
        #
        for event in pygame.event.get():    # we can capture any event (mouse movement, times, buttons)
            if event.type == pygame.QUIT:
                exit_app()
            if event.type == pygame.KEYDOWN:    # map key press handlers
                if input_active:
                    if event.key == pygame.K_RETURN:
                        if len(player_name) > 0:
                            update_highscore()
                            input_active = False
                            reset_game()
                            player_name = ''
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    elif len(player_name) < MAX_NAME_LENGTH and event.unicode.isalnum():
                        player_name += event.unicode
                if event.key == pygame.K_ESCAPE:
                    exit_app()
            if event.type == pygame.MOUSEBUTTONDOWN and not input_active:
                action()
            if event.type == SPAWNPIPE_EVT:  # handle custom events
                pipe_rect_list.extend(create_pipe())  # add generated pipes tuple to the list
            if event.type == BIRD_FLAP_EVT:
                bird_animation()

        ############
        # placing assets
        # [wip] export all to sub functions?
        #

        # place background: this will be static and not redrawn in the game loop
        screen.blit(bg_surface, (0,0))  # [demo] origin of the surfaces is the top left, rectangle geometry will place the surface


        # the game  will have two modes: .... [wip]
        # elements in an active game
        if (game_active):
            # placing the bird
            bird_speed += gravity    # move the bird, maintain falling acceleration
            bird_rect.centery += bird_speed
            bird_rotated = rotate_bird(bird_surface)    # bird rotation animation
            draw_bird(bird_rotated) # finally, draw the moving, rotated bird

            game_active = check_collisions(pipe_rect_list)

            # placing the pipes
            # [wip] parametrize this list properly
            pipe_rect_list = move_pipes(pipe_rect_list)
            draw_pipes(pipe_rect_list)

            # placing the score
            game_score +=1  # [wip] option: count score as pipes passed, add the sound [here] ...
            #game_score_sound.play()
        else:
            draw_highscore()
            screen.blit(greeting_surface, greeting_rect)

        # Handle input active
        if input_active:
            prompt_text = f'Enter Name: {player_name}_'
            prompt_surface = game_font.render(prompt_text, True, COLOR_RGB)
            prompt_rect = prompt_surface.get_rect(center=(SCORE_X, HIGHSCORE_Y - 50))
            screen.blit(prompt_surface, prompt_rect)

        draw_score()

        # placing the floor (it comes after the pipes so it will be drawn above)
        # the floor will be moving regardless the game state
        # [wip] move to function?
        floor_x -= FLOOR_SPEED
        # reset moving floor
        if (floor_x <= -DISPLAY_WIDTH):
            floor_x = 0
        # [debug] print ("floor_x: " + str(floor_x))
        draw_floor()


        ############
        # redraw the canvas
        #
        pygame.display.update()
        # set frame rate. some complex games may require frame limiting
        clock.tick(FPS)
        await asyncio.sleep(0)


asyncio.run(main())
# pygame.quit()