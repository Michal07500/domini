# # # EFEKTY # # #
# Častice, vyskakujúci text a tlaková vlna bomby #

import math
import random

import pygame

from grafika import FONT_SMALL


class Particle:
    def __init__(self, x, y, vx, vy, life, color, size):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color, self.size = color, size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.94
        self.vy *= 0.94
        self.life -= 1

    def draw(self, surf):
        size = max(2, int(self.size * self.life / self.max_life) * 2)
        surf.fill(self.color, (int(self.x) - size // 2, int(self.y) - size // 2, size, size))


def burst(particles, x, y, count, colors, speed=4, life=35, size=4):
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        v = random.uniform(0.5, speed)
        particles.append(Particle(x, y, math.cos(angle) * v, math.sin(angle) * v,
                                  random.randint(life // 2, life), random.choice(colors), size))


class FloatingText:
    def __init__(self, x, y, text, color):
        self.image = FONT_SMALL.render(text, False, color)
        self.x, self.y = x, y
        self.life = 50

    def update(self):
        self.y -= 0.8
        self.life -= 1

    def draw(self, surf):
        self.image.set_alpha(min(255, self.life * 8))
        surf.blit(self.image, self.image.get_rect(center=(self.x, self.y)))


class Shockwave:
    def __init__(self, x, y, color, max_radius=700):
        self.x, self.y, self.color = x, y, color
        self.radius = 10
        self.max_radius = max_radius

    @property
    def life(self):
        return self.max_radius - self.radius

    def update(self):
        self.radius += 22

    def draw(self, surf):
        width = max(2, int(12 * self.life / self.max_radius))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), int(self.radius), width)
