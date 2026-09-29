# # # GRAFIKA # # #
# Fonty, pixelové sprity, pozadie a VHS efekt #

import math
import random

import pygame

from nastavenia import *

# Fonty – strojopisné písmo bez vyhladzovania vyzerá ako text na starom VHS #

FONT_NAMES = "dejavusansmono,consolas,couriernew,lucidaconsole,monospace"
FONT_SMALL = pygame.font.SysFont(FONT_NAMES, 18, bold=True)
FONT = pygame.font.SysFont(FONT_NAMES, 26, bold=True)
FONT_BIG = pygame.font.SysFont(FONT_NAMES, 42, bold=True)
FONT_HUGE = pygame.font.SysFont(FONT_NAMES, 70, bold=True)

# # # POMOCNÉ FUNKCIE # # #

def draw_text(surf, text, font, color, pos, anchor="center", shadow=True):
    img = font.render(text, False, color)
    rect = img.get_rect(**{anchor: pos})
    if shadow:
        surf.blit(font.render(text, False, BLACK), rect.move(3, 3))
    surf.blit(img, rect)
    return rect


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def dim(color, k):
    return tuple(min(255, int(c * k)) for c in color)


_glow_cache = {}


def blit_glow(surf, radius, color, center, strength=1.0):
    # Žiara = kruh, ktorý smerom von tmavne a pripočíta sa k farbe pod ním #
    radius = int(radius)
    key = (radius, color, strength)
    if key not in _glow_cache:
        glow = pygame.Surface((radius * 2, radius * 2))
        for r in range(radius, 0, -1):
            k = (1 - r / radius) ** 2 * strength
            pygame.draw.circle(glow, [min(255, int(c * k)) for c in color], (radius, radius), r)
        _glow_cache[key] = glow
    surf.blit(_glow_cache[key], (center[0] - radius, center[1] - radius), special_flags=pygame.BLEND_RGB_ADD)


def make_sprite(rows, palette, scale):
    # Z textového obrázka (každé písmeno = jedna farba) spraví pixelový sprite #
    width = max(len(row) for row in rows)
    surf = pygame.Surface((width * scale, len(rows) * scale), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            color = palette.get(ch)
            if color:
                surf.fill(color, (x * scale, y * scale, scale, scale))
    return surf


def silhouette(rows, color, scale):
    return make_sprite(rows, {ch: color for row in rows for ch in row if ch != "."}, scale)


def timecode(ms):
    seconds = int(ms // 1000)
    return f"{seconds // 3600}:{seconds // 60 % 60:02}:{seconds % 60:02}"

# # # IKONKY # # #

HEART_ROWS = [
    ".pp.pp.",
    "pwppppp",
    "ppppppp",
    ".ppppp.",
    "..ppp..",
    "...p...",
]
HEART_FULL = make_sprite(HEART_ROWS, {"p": PINK, "w": WHITE}, 3)
HEART_EMPTY = make_sprite(HEART_ROWS, {"p": (60, 50, 80), "w": (80, 70, 100)}, 3)


def draw_play_icon(surf, x, y, h, color):
    pygame.draw.polygon(surf, color, [(x, y - h // 2), (x, y + h // 2), (x + h * 0.85, y)])


def draw_pause_icon(surf, x, y, h, color):
    pygame.draw.rect(surf, color, (x, y - h // 2, h // 3, h))
    pygame.draw.rect(surf, color, (x + h // 2, y - h // 2, h // 3, h))


def draw_rewind_icon(surf, x, y, h, color):
    for dx in (0, h * 0.7):
        pygame.draw.polygon(surf, color, [(x + dx + h * 0.7, y - h // 2), (x + dx + h * 0.7, y + h // 2), (x + dx, y)])

# # # POZADIE # # #

class Background:
    # Retro "synthwave" krajina: nebo so slnkom a ubiehajúca mriežka #
    def __init__(self, theme):
        self.offset = 0
        self.set_theme(theme)

    def set_theme(self, theme):
        self.theme = theme
        self.horizon = int(HEIGHT * 0.48)
        surf = pygame.Surface((WIDTH, HEIGHT))
        top, bottom = theme["sky"]
        for y in range(self.horizon):
            pygame.draw.line(surf, lerp_color(top, bottom, y / self.horizon), (0, y), (WIDTH, y))
        surf.fill(theme["floor"], (0, self.horizon, WIDTH, HEIGHT - self.horizon))

        # Pruhované slnko #
        r = 130
        c1, c2 = theme["sun"]
        for dy in range(-r, 0):
            t = (dy + r) / r
            if t > 0.45 and (dy + r) % 16 < (t - 0.45) * 22:
                continue
            half = math.sqrt(r * r - dy * dy)
            pygame.draw.line(surf, dim(lerp_color(c1, c2, t), 0.55),
                             (WIDTH / 2 - half, self.horizon + dy), (WIDTH / 2 + half, self.horizon + dy))
        self.surface = surf.convert() if pygame.display.get_surface() else surf
        self.stars = [[random.uniform(0, WIDTH), random.uniform(0, self.horizon - 10), random.uniform(0.2, 1.2)]
                      for _ in range(90)]

    def update(self, speed=1.0):
        for star in self.stars:
            star[0] -= star[2] * 0.3 * speed
            if star[0] < 0:
                star[0] = WIDTH
        self.offset = (self.offset + 0.006 * speed) % 1

    def draw(self, surf):
        surf.blit(self.surface, (0, 0))
        for x, y, speed in self.stars:
            b = int(90 + 120 * speed / 1.2)
            surf.fill((b, b, min(255, b + 30)), (int(x), int(y), 2, 2))
        grid = self.theme["grid"]
        horizon, cx = self.horizon, WIDTH // 2
        for i in range(-14, 15):
            pygame.draw.line(surf, grid, (cx + i * 24, horizon), (cx + i * 150, HEIGHT), 2)
        for k in range(12):
            t = (k + self.offset) / 12
            y = horizon + (HEIGHT - horizon) * t * t
            pygame.draw.line(surf, grid, (0, y), (WIDTH, y), 2)
        pygame.draw.line(surf, dim(self.theme["sun"][1], 0.8), (0, horizon), (WIDTH, horizon), 2)

# # # VHS EFEKT # # #

class VhsFilter:
    # Zväčšené pixely, posunuté farby, riadky, tmavé rohy a občasné "trhanie" pásky #
    def __init__(self):
        self.small_size = (WIDTH // PIXEL, HEIGHT // PIXEL)

        # Riadky a tmavé rohy sú v jednej "násobiacej" vrstve (rýchlejšie ako priehľadnosť) #
        small = pygame.Surface((40, 28))
        for y in range(28):
            for x in range(40):
                d = math.hypot((x + 0.5) / 20 - 1, (y + 0.5) / 14 - 1)
                v = int(255 * (1 - max(0.0, min(1.0, (d - 0.75) / 0.7)) * 0.8))
                small.set_at((x, y), (v, v, v))
        self.overlay = pygame.transform.smoothscale(small, (WIDTH, HEIGHT))
        for y in range(0, HEIGHT, PIXEL * 2):
            self.overlay.fill((200, 200, 200), (0, y + PIXEL, WIDTH, PIXEL), special_flags=pygame.BLEND_RGB_MULT)
        if pygame.display.get_surface():
            self.overlay = self.overlay.convert()

        self.roll_band = pygame.Surface((self.small_size[0], 70))
        for i in range(70):
            v = int(10 * math.sin(math.pi * i / 70))
            self.roll_band.fill((v, v, v), (0, i, self.small_size[0], 1))

        self.roll = 0
        self.glitch = 0
        self.track = 0

    def kick(self, amount):
        self.glitch = max(self.glitch, amount)
        self.track = max(self.track, int(amount))

    def apply(self, canvas):
        w, h = self.small_size
        small = pygame.transform.smoothscale(canvas, self.small_size)

        # Posun červenej farby (chromatická aberácia) #
        red = small.copy()
        red.fill((255, 0, 0), special_flags=pygame.BLEND_MULT)
        small.fill((0, 255, 255), special_flags=pygame.BLEND_MULT)
        small.blit(red, (1 + int(self.glitch) // PIXEL, 0), special_flags=pygame.BLEND_ADD)

        # Pomaly sa posúvajúci svetlý pás #
        self.roll = (self.roll + 0.6) % (h + 70)
        small.blit(self.roll_band, (0, int(self.roll) - 70), special_flags=pygame.BLEND_RGB_ADD)

        # Trhanie obrazu #
        if self.track <= 0 and random.random() < 0.004:
            self.track = random.randint(3, 8)
        if self.track > 0:
            self.track -= 1
            band_h = random.randint(4, 12 + int(self.glitch) * 2)
            y = random.randrange(0, h - band_h)
            band = small.subsurface((0, y, w, band_h)).copy()
            small.blit(band, (random.randint(-5, 5) * (1 + int(self.glitch) // 3), y))
            for _ in range(25):
                small.fill((200, 200, 210), (random.randrange(w), y + random.randrange(band_h), random.randint(1, 5), 1))

        frame = pygame.transform.scale(small, (WIDTH, HEIGHT))
        frame.blit(self.overlay, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        self.glitch *= 0.9
        return frame
