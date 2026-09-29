# # # STRELY # # #

import math

import pygame

from grafika import blit_glow
from nastavenia import WHITE


def circle_hits_rect(cx, cy, radius, rect):
    nx = max(rect.left, min(cx, rect.right))
    ny = max(rect.top, min(cy, rect.bottom))
    return (cx - nx) ** 2 + (cy - ny) ** 2 <= radius ** 2


class Bullet:
    def __init__(self, x, y, vx, vy, radius, color, delay=0, homing=0.0, homing_frames=0,
                 reverse_after=0, life=None, damage=1):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.radius, self.color = radius, color
        self.dim_color = tuple(c // 2 for c in color)
        self.delay = delay            # kým beží odpočet, strela len bliká ako varovanie
        self.homing = homing          # o koľko sa môže za snímok natočiť k cieľu
        self.homing_frames = homing_frames
        self.reverse_after = reverse_after  # "pretočenie pásky" – strela sa po čase vráti
        self.life = life              # laser zmizne po určitom čase
        self.damage = damage
        self.crit = False
        self.dead = False
        self.age = 0
        self.trail = []

    @property
    def active(self):
        return self.delay <= 0

    def update(self, dt, target=None):
        if self.delay > 0:
            self.delay -= dt
            return
        self.age += 1

        if self.homing and target is not None and self.age <= self.homing_frames:
            speed = math.hypot(self.vx, self.vy)
            current = math.atan2(self.vy, self.vx)
            wanted = math.atan2(target.y - self.y, target.x - self.x)
            diff = (wanted - current + math.pi) % math.tau - math.pi
            current += max(-self.homing, min(self.homing, diff))
            self.vx, self.vy = math.cos(current) * speed, math.sin(current) * speed

        if self.reverse_after and self.age == self.reverse_after:
            self.vx, self.vy = -self.vx, -self.vy

        if self.life is not None:
            self.life -= dt
            if self.life <= 0:
                self.dead = True

        if self.vx or self.vy:
            self.trail.append((self.x, self.y))
            if len(self.trail) > 6:
                self.trail.pop(0)
        self.x += self.vx
        self.y += self.vy

    def outside(self, rect, margin=0):
        return not rect.inflate(margin * 2, margin * 2).collidepoint(self.x, self.y)

    def draw(self, surf, now):
        pos = (int(self.x), int(self.y))
        if self.delay > 0:
            if (now // 100) % 2 == 0:
                if self.vx or self.vy:
                    pygame.draw.circle(surf, self.color, pos, self.radius + 4, 2)
                    end = (int(self.x + self.vx * 12), int(self.y + self.vy * 12))
                    pygame.draw.line(surf, self.color, pos, end, 2)
                else:
                    surf.fill(self.color, (pos[0] - 3, pos[1] - 3, 6, 6))
            return
        for i, (tx, ty) in enumerate(self.trail):
            r = max(1, int(self.radius * (i + 1) / len(self.trail) * 0.6))
            pygame.draw.circle(surf, self.dim_color, (int(tx), int(ty)), r)
        blit_glow(surf, self.radius * 3, self.color, pos, 0.8)
        pygame.draw.circle(surf, self.color, pos, self.radius)
        pygame.draw.circle(surf, WHITE, pos, max(1, self.radius // 2))
