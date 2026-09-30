# # # HRÁČ # # #

import math
import random

import pygame

from grafika import blit_glow, make_sprite
from nastavenia import *
from strely import Bullet

PLAYER_ROWS = [
    "..kkkkkk..",
    ".kcccccck.",
    "kcbbbbbbck",
    "kcbwbbwbck",
    "kcbbbbbbck",
    "kcccccccck",
    ".kcppppck.",
    ".kcccccck.",
    "..kc..ck..",
    "..kk..kk..",
]
PLAYER_SPRITE = make_sprite(PLAYER_ROWS, {"k": (10, 20, 40), "c": CYAN, "b": (20, 40, 90), "w": WHITE, "p": PINK}, 3)
PLAYER_GHOST = make_sprite(PLAYER_ROWS, {ch: (*CYAN, 90) for ch in "kcbwp"}, 3)


class Player:
    def __init__(self, max_health):
        self.upgrades = {}
        self.health = self.max_health = max_health
        self.bomb_charge = 0.0
        self.shield = False
        self.start_level()

    # Hodnoty, ktoré sa menia podľa vylepšení #

    def level(self, key):
        return self.upgrades.get(key, 0)

    @property
    def bullet_delay(self):
        return BULLET_DELAY * 0.8 ** self.level("rate")

    @property
    def speed(self):
        return PLAYER_VEL + 0.8 * self.level("speed")

    @property
    def dash_cooldown(self):
        return DASH_COOLDOWN * 0.65 ** self.level("dash")

    @property
    def shield_cooldown(self):
        return SHIELD_COOLDOWN - 4000 * (self.level("shield") - 1)

    @property
    def bomb_damage(self):
        return BOMB_DAMAGE + 4 * self.level("bomb")

    def add_upgrade(self, key):
        self.upgrades[key] = self.level(key) + 1
        if key == "heart":
            self.max_health += 1
            self.health += 1
        elif key == "heal":
            self.health = self.max_health
        elif key == "shield":
            self.shield = True

    # Príprava na novú kazetu #

    def start_level(self):
        self.x = ARENA.centerx
        self.y = ARENA.top + ARENA.height * 0.75
        self.invincible_until = 0
        self.next_shot = 0
        self.dash_until = 0
        self.next_dash = 0
        self.dash_dir = (0, -1)
        self.last_move = (0, -1)
        self.facing = (0, -1)
        self.afterimages = []
        self.shield_ready_at = 0
        if self.level("shield"):
            self.shield = True

    @property
    def rect(self):
        return pygame.Rect(self.x - PLAYER_SIZE / 2, self.y - PLAYER_SIZE / 2, PLAYER_SIZE, PLAYER_SIZE)

    @property
    def hitbox(self):
        return pygame.Rect(self.x - PLAYER_HITBOX / 2, self.y - PLAYER_HITBOX / 2, PLAYER_HITBOX, PLAYER_HITBOX)

    def is_invincible(self, now):
        return now < self.invincible_until or now < self.dash_until

    def take_hit(self, now):
        # Vráti True, ak hráč prišiel o život (štít zásah zachytí) #
        if self.shield:
            self.shield = False
            self.shield_ready_at = now + self.shield_cooldown
            self.invincible_until = now + I_FRAMES // 2
            return False
        self.health -= 1
        self.invincible_until = now + I_FRAMES
        return True

    @staticmethod
    def input_dir(keys):
        dx = keys[pygame.K_d] - keys[pygame.K_a]
        dy = keys[pygame.K_s] - keys[pygame.K_w]
        if dx and dy:  # šikmo sa hráč nehýbe rýchlejšie
            dx *= 0.7071
            dy *= 0.7071
        return dx, dy

    def clamp(self):
        half = PLAYER_SIZE / 2
        self.x = max(ARENA.left + half, min(ARENA.right - half, self.x))
        self.y = max(ARENA.top + half, min(ARENA.bottom - half, self.y))

    def try_dash(self, keys, now):
        if now < self.next_dash:
            return False
        dx, dy = self.input_dir(keys)
        self.dash_dir = (dx, dy) if (dx or dy) else self.last_move
        self.dash_until = now + DASH_TIME
        self.next_dash = now + self.dash_cooldown
        return True

    def update(self, keys, now):
        if now < self.dash_until:
            self.x += self.dash_dir[0] * DASH_SPEED
            self.y += self.dash_dir[1] * DASH_SPEED
            self.afterimages.append([self.x, self.y, 180])
        else:
            dx, dy = self.input_dir(keys)
            if dx or dy:
                self.last_move = (dx, dy)
            self.x += dx * self.speed
            self.y += dy * self.speed
        self.clamp()
        for image in self.afterimages:
            image[2] -= 20
        self.afterimages = [a for a in self.afterimages if a[2] > 0]
        if self.level("shield") and not self.shield and now >= self.shield_ready_at:
            self.shield = True

    def try_shoot(self, keys, now):
        if now < self.next_shot:
            return []
        sx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        sy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
        if not sx and not sy:
            return []
        base = math.atan2(sy, sx)
        self.next_shot = now + self.bullet_delay
        self.facing = (math.cos(base), math.sin(base))

        # Spätný ráz – hráča to pri streľbe trochu odtlačí (ako v pôvodnej hre) #
        self.x -= self.facing[0] * RECOIL
        self.y -= self.facing[1] * RECOIL
        self.clamp()

        count = 1 + self.level("multi")
        angles = [base + (i - (count - 1) / 2) * 0.16 for i in range(count)]
        if self.level("back"):
            angles.append(base + math.pi)

        bullets = []
        radius = 5 + 2 * self.level("size")
        speed = PLAYER_BULLET_VEL + 2 * self.level("size")
        for a in angles:
            bullet = Bullet(self.x + math.cos(a) * 18, self.y + math.sin(a) * 18,
                            math.cos(a) * speed, math.sin(a) * speed, radius, LIGHT_CYAN,
                            homing=0.05 * self.level("homing"), homing_frames=45,
                            damage=1 + self.level("damage"))
            if random.random() < 0.2 * self.level("crit"):
                bullet.crit = True
                bullet.damage *= 2
                bullet.color = GOLD
                bullet.dim_color = (128, 105, 40)
            bullets.append(bullet)
        return bullets

    def draw(self, surf, now):
        for x, y, alpha in self.afterimages:
            PLAYER_GHOST.set_alpha(alpha)
            surf.blit(PLAYER_GHOST, PLAYER_GHOST.get_rect(center=(int(x), int(y))))
        if now < self.invincible_until and (now // 80) % 2:
            return  # blikanie počas nezraniteľnosti
        center = (int(self.x), int(self.y))
        blit_glow(surf, 42, CYAN, center, 0.6)
        surf.blit(PLAYER_SPRITE, PLAYER_SPRITE.get_rect(center=center))
        if self.shield:
            r = 24 + int(math.sin(now / 120) * 2)
            pygame.draw.circle(surf, BLUE, center, r, 2)
            pygame.draw.circle(surf, LIGHT_CYAN, center, r + 3, 1)
