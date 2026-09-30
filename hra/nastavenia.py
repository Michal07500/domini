# # # NASTAVENIA HRY # # #
# Všetky nemeniteľné hodnoty sú na jednom mieste, aby sa hra dala ľahko ladiť. #

import os

import pygame

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

# Okno a hracia plocha #

WIDTH, HEIGHT = 1000, 700
FPS = 60
ARENA = pygame.Rect(20, 70, WIDTH - 40, HEIGHT - 110)
PIXEL = 2  # o koľko sa obraz zmenší pri VHS efekte (väčšie číslo = hrubšie pixely)

# Hráč #

PLAYER_SIZE = 30
PLAYER_HITBOX = 16  # menší hitbox, aby sa dalo férovo uhýbať
PLAYER_VEL = 5
PLAYER_BULLET_VEL = 11
RECOIL = 3
DASH_SPEED = 15

# Časy (v milisekundách) #

BULLET_DELAY = 300
I_FRAMES = 1000
DASH_TIME = 140
DASH_COOLDOWN = 900
SHIELD_COOLDOWN = 12000
MOVE_DELAY = 1500
ATTACK_WAVE_DELAY = 500
WARNING_TIME = 650
LASER_WARNING = 750
LASER_TIME = 450
END_DELAY = 2200

# Bomba #

BOMB_HITS = 35  # koľko zásahov treba na nabitie bomby
BOMB_DAMAGE = 6

# Skóre #

HIT_SCORE = 50
MISS_SCORE = -10
HURT_SCORE = -100
KILL_SCORE = 500  # násobí sa číslom kazety
BOMB_BULLET_SCORE = 5

# Obtiažnosti #

DIFFICULTIES = [
    {"name": "Ľahká", "player_health": 6, "boss_health": 35, "bullet_vel": 3.3, "attack_delay": 2300, "mult": 0.8},
    {"name": "Normálna", "player_health": 5, "boss_health": 45, "bullet_vel": 4.0, "attack_delay": 1900, "mult": 1.0},
    {"name": "Ťažká", "player_health": 4, "boss_health": 60, "bullet_vel": 4.7, "attack_delay": 1500, "mult": 1.5},
]

# Farby #

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (150, 150, 175)
DARK = (20, 18, 40)
ARENA_BORDER = (110, 80, 170)
CYAN = (70, 220, 255)
LIGHT_CYAN = (190, 250, 255)
DARK_CYAN = (20, 90, 120)
BLUE = (80, 140, 255)
RED = (255, 60, 90)
DARK_RED = (120, 20, 40)
ORANGE = (255, 150, 40)
PINK = (255, 110, 160)
MAGENTA = (255, 80, 230)
GOLD = (255, 210, 80)
YELLOW = (255, 235, 90)
GREEN = (100, 235, 140)
LIME = (170, 255, 90)
LILAC = (200, 160, 255)
TEAL = (90, 255, 210)

# Prostredia jednotlivých kaziet (farba neba, podlahy, mriežky a slnka) #

THEMES = [
    {"sky": ((12, 8, 30), (70, 20, 80)), "floor": (16, 6, 30), "grid": (90, 30, 110),
     "sun": ((255, 210, 90), (255, 60, 150)), "accent": PINK},
    {"sky": ((2, 4, 16), (10, 40, 50)), "floor": (4, 14, 20), "grid": (20, 90, 80),
     "sun": ((170, 255, 190), (40, 130, 210)), "accent": GREEN},
    {"sky": ((6, 4, 16), (40, 28, 70)), "floor": (10, 8, 22), "grid": (60, 50, 110),
     "sun": ((240, 240, 255), (150, 140, 210)), "accent": LILAC},
    {"sky": ((14, 10, 8), (70, 40, 20)), "floor": (18, 12, 8), "grid": (110, 60, 20),
     "sun": ((255, 200, 80), (210, 60, 20)), "accent": ORANGE},
    {"sky": ((20, 0, 12), (80, 0, 50)), "floor": (18, 0, 14), "grid": (130, 20, 90),
     "sun": ((255, 90, 170), (90, 220, 255)), "accent": MAGENTA},
]

# Súbor s uloženým postupom a najlepším skóre #

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ulozenie.json")
