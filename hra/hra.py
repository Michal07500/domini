# # # IMPORTOVANIA # # #

import array
import json
import math
import os
import random

import pygame

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

# # # NEMENITEĽNÉ HODNOTY # # #

# Okno a hracia plocha #

WIDTH, HEIGHT = 1000, 700
FPS = 60
ARENA = pygame.Rect(20, 70, WIDTH - 40, HEIGHT - 110)

# Veľkosti #

PLAYER_SIZE = 30
PLAYER_HITBOX = 18  # menší hitbox, aby sa dalo férovo uhýbať
BOSS_SIZE = 70

# Rýchlosti #

PLAYER_VEL = 5
PLAYER_BULLET_VEL = 11
RECOIL = 4
BOSS_VEL = 2.2
DASH_SPEED = 15

# Časy (v milisekundách) #

BULLET_DELAY = 280
I_FRAMES = 1000
DASH_TIME = 140
DASH_COOLDOWN = 900
MOVE_DELAY = 1500
ATTACK_WAVE_DELAY = 500
WARNING_TIME = 650
END_DELAY = 2200

# Skóre #

HIT_SCORE = 50
MISS_SCORE = -10
HURT_SCORE = -100
KILL_SCORE = 500

# Obtiažnosti #

DIFFICULTIES = [
    {"name": "Ľahká", "player_health": 7, "boss_health": 40, "bullet_vel": 3.3, "attack_delay": 2300, "mult": 0.8},
    {"name": "Normálna", "player_health": 5, "boss_health": 50, "bullet_vel": 4.0, "attack_delay": 1900, "mult": 1.0},
    {"name": "Ťažká", "player_health": 4, "boss_health": 70, "bullet_vel": 4.8, "attack_delay": 1500, "mult": 1.5},
]

# Farby #

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BG_TOP = (10, 10, 28)
BG_BOTTOM = (38, 14, 54)
GRID = (30, 24, 62)
ARENA_BORDER = (90, 70, 160)
CYAN = (70, 220, 255)
LIGHT_CYAN = (190, 250, 255)
DARK_CYAN = (20, 90, 120)
RED = (255, 60, 90)
DARK_RED = (120, 20, 40)
ORANGE = (255, 150, 40)
DARK_ORANGE = (140, 60, 10)
PINK = (255, 110, 160)
GOLD = (255, 210, 80)
GREEN = (100, 235, 140)
GREY = (150, 150, 175)
DARK = (20, 18, 40)

# Súbor s najlepším skóre #

HIGHSCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.json")

# # # VECI # # #

# Okienko #

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hra na ročníkovú prácu")

# Fonty #

FONT_NAMES = "dejavusans,segoeui,arial,verdana"
FONT_SMALL = pygame.font.SysFont(FONT_NAMES, 20)
FONT = pygame.font.SysFont(FONT_NAMES, 28)
FONT_BIG = pygame.font.SysFont(FONT_NAMES, 44, bold=True)
FONT_HUGE = pygame.font.SysFont(FONT_NAMES, 80, bold=True)

# # # POMOCNÉ FUNKCIE # # #

def draw_text(surf, text, font, color, pos, anchor="center", shadow=True):
    img = font.render(text, True, color)
    rect = img.get_rect(**{anchor: pos})
    if shadow:
        surf.blit(font.render(text, True, BLACK), rect.move(3, 3))
    surf.blit(img, rect)
    return rect


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


def draw_heart(surf, x, y, size, color):
    r = size // 4
    pygame.draw.circle(surf, color, (x - r, y - r // 2), r + 1)
    pygame.draw.circle(surf, color, (x + r, y - r // 2), r + 1)
    pygame.draw.polygon(surf, color, [(x - 2 * r - 1, y - r // 3), (x + 2 * r + 1, y - r // 3), (x, y + 2 * r)])


def circle_hits_rect(cx, cy, radius, rect):
    nx = max(rect.left, min(cx, rect.right))
    ny = max(rect.top, min(cy, rect.bottom))
    return (cx - nx) ** 2 + (cy - ny) ** 2 <= radius ** 2


def load_highscores():
    try:
        with open(HIGHSCORE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_highscores(highscores):
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
            json.dump(highscores, f, ensure_ascii=False, indent=2)
    except OSError:
        pass

# # # ZVUKY # # #

class Sounds:
    # Zvuky sa generujú priamo v kóde, takže hra nepotrebuje žiadne súbory #
    def __init__(self):
        self.enabled = True
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            rate, _, channels = pygame.mixer.get_init()
            self.sounds = {
                "shoot": self.synth(rate, channels, 900, 500, 0.06, 0.10),
                "hit": self.synth(rate, channels, 320, 120, 0.08, 0.18),
                "hurt": self.synth(rate, channels, 0, 0, 0.30, 0.35, noise=True),
                "boss_shot": self.synth(rate, channels, 240, 160, 0.10, 0.08, wave="sine"),
                "explode": self.synth(rate, channels, 0, 0, 1.00, 0.45, noise=True),
                "select": self.synth(rate, channels, 520, 880, 0.10, 0.18),
                "move": self.synth(rate, channels, 420, 420, 0.04, 0.10),
                "phase": self.synth(rate, channels, 90, 420, 0.70, 0.30),
                "dash": self.synth(rate, channels, 0, 0, 0.12, 0.15, noise=True),
            }
        except (pygame.error, TypeError):
            self.sounds = {}

    @staticmethod
    def synth(rate, channels, f_start, f_end, duration, volume, wave="square", noise=False):
        samples = int(rate * duration)
        buf = array.array("h")
        phase = 0.0
        for i in range(samples):
            t = i / samples
            phase += (f_start + (f_end - f_start) * t) / rate
            if noise:
                value = random.uniform(-1, 1)
            elif wave == "square":
                value = 1.0 if phase % 1 < 0.5 else -1.0
            else:
                value = math.sin(phase * math.tau)
            sample = int(value * (1 - t) ** 2 * volume * 32767)
            for _ in range(channels):
                buf.append(sample)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def toggle(self):
        self.enabled = not self.enabled

# # # POZADIE # # #

class Background:
    def __init__(self):
        self.surface = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            t = y / HEIGHT
            color = [int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)]
            pygame.draw.line(self.surface, color, (0, y), (WIDTH, y))
        self.stars = [[random.uniform(0, WIDTH), random.uniform(0, HEIGHT), random.uniform(0.2, 1.5)]
                      for _ in range(120)]
        self.grid_offset = 0

    def update(self, speed=1.0):
        for star in self.stars:
            star[1] += star[2] * speed
            if star[1] > HEIGHT:
                star[0], star[1] = random.uniform(0, WIDTH), 0
        self.grid_offset = (self.grid_offset + 0.4 * speed) % 50

    def draw(self, surf):
        surf.blit(self.surface, (0, 0))
        for x in range(0, WIDTH, 50):
            pygame.draw.line(surf, GRID, (x, 0), (x, HEIGHT))
        for y in range(int(self.grid_offset) - 50, HEIGHT, 50):
            pygame.draw.line(surf, GRID, (0, y), (WIDTH, y))
        for x, y, speed in self.stars:
            b = int(70 + 120 * speed / 1.5)
            pygame.draw.circle(surf, (b, b, min(255, b + 40)), (int(x), int(y)), 1 if speed < 1 else 2)

# # # EFEKTY # # #

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
        radius = max(1, int(self.size * self.life / self.max_life))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), radius)


def burst(particles, x, y, count, colors, speed=4, life=35, size=4):
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        v = random.uniform(0.5, speed)
        particles.append(Particle(x, y, math.cos(angle) * v, math.sin(angle) * v,
                                  random.randint(life // 2, life), random.choice(colors), size))


class FloatingText:
    def __init__(self, x, y, text, color):
        self.image = FONT_SMALL.render(text, True, color)
        self.x, self.y = x, y
        self.life = 50

    def update(self):
        self.y -= 0.8
        self.life -= 1

    def draw(self, surf):
        self.image.set_alpha(min(255, self.life * 8))
        surf.blit(self.image, self.image.get_rect(center=(self.x, self.y)))

# # # STRELY # # #

class Bullet:
    def __init__(self, x, y, vx, vy, radius, color, delay=0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.radius, self.color = radius, color
        self.dim_color = tuple(c // 2 for c in color)
        self.delay = delay  # kým beží odpočet, strela len bliká ako varovanie
        self.trail = []

    @property
    def active(self):
        return self.delay <= 0

    def update(self, dt):
        if self.delay > 0:
            self.delay -= dt
            return
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
                pygame.draw.circle(surf, self.color, pos, self.radius + 4, 2)
                end = (int(self.x + self.vx * 12), int(self.y + self.vy * 12))
                pygame.draw.line(surf, self.color, pos, end, 2)
            return
        for i, (tx, ty) in enumerate(self.trail):
            r = max(1, int(self.radius * (i + 1) / len(self.trail) * 0.6))
            pygame.draw.circle(surf, self.dim_color, (int(tx), int(ty)), r)
        blit_glow(surf, self.radius * 3, self.color, pos, 0.8)
        pygame.draw.circle(surf, self.color, pos, self.radius)
        pygame.draw.circle(surf, WHITE, pos, max(1, self.radius // 2))

# # # HRÁČ # # #

class Player:
    def __init__(self, max_health):
        self.x = ARENA.centerx
        self.y = ARENA.top + ARENA.height * 0.75
        self.health = self.max_health = max_health
        self.invincible_until = 0
        self.next_shot = 0
        self.dash_until = 0
        self.next_dash = 0
        self.dash_dir = (0, -1)
        self.last_move = (0, -1)
        self.facing = (0, -1)
        self.afterimages = []

    @property
    def rect(self):
        return pygame.Rect(self.x - PLAYER_SIZE / 2, self.y - PLAYER_SIZE / 2, PLAYER_SIZE, PLAYER_SIZE)

    @property
    def hitbox(self):
        return pygame.Rect(self.x - PLAYER_HITBOX / 2, self.y - PLAYER_HITBOX / 2, PLAYER_HITBOX, PLAYER_HITBOX)

    def is_invincible(self, now):
        return now < self.invincible_until or now < self.dash_until

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
        self.next_dash = now + DASH_COOLDOWN
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
            self.x += dx * PLAYER_VEL
            self.y += dy * PLAYER_VEL
        self.clamp()
        for image in self.afterimages:
            image[2] -= 20
        self.afterimages = [a for a in self.afterimages if a[2] > 0]

    def try_shoot(self, keys, now):
        if now < self.next_shot:
            return None
        sx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        sy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
        if not sx and not sy:
            return None
        length = math.hypot(sx, sy)
        sx, sy = sx / length, sy / length
        self.next_shot = now + BULLET_DELAY
        self.facing = (sx, sy)
        # Spätný ráz – hráča to pri streľbe trochu odtlačí (ako v pôvodnej hre) #
        self.x -= sx * RECOIL
        self.y -= sy * RECOIL
        self.clamp()
        return Bullet(self.x + sx * 18, self.y + sy * 18, sx * PLAYER_BULLET_VEL, sy * PLAYER_BULLET_VEL, 5, LIGHT_CYAN)

    def draw(self, surf, now):
        for x, y, alpha in self.afterimages:
            ghost = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(ghost, (*CYAN, alpha // 2), ghost.get_rect(), border_radius=7)
            surf.blit(ghost, (x - PLAYER_SIZE / 2, y - PLAYER_SIZE / 2))
        if now < self.invincible_until and (now // 80) % 2:
            return  # blikanie počas nezraniteľnosti
        center = (int(self.x), int(self.y))
        blit_glow(surf, 42, CYAN, center, 0.6)
        body = self.rect
        pygame.draw.rect(surf, DARK_CYAN, body.inflate(6, 6), border_radius=9)
        pygame.draw.rect(surf, CYAN, body, border_radius=7)
        pygame.draw.rect(surf, LIGHT_CYAN, body.inflate(-12, -12), border_radius=4)
        fx, fy = self.facing
        for ex in (-5, 5):
            pygame.draw.circle(surf, DARK, (int(self.x + ex + fx * 3), int(self.y - 1 + fy * 3)), 3)

# # # NEPRIATEĽ # # #

class Boss:
    def __init__(self, difficulty, bullets, sounds, now=0):
        self.x = ARENA.centerx
        self.y = ARENA.top + 130
        self.health = self.max_health = difficulty["boss_health"]
        self.shown_health = float(self.health)  # pomaly klesajúci pásik životov
        self.bullet_vel = difficulty["bullet_vel"]
        self.attack_delay = difficulty["attack_delay"]
        self.bullets = bullets
        self.sounds = sounds
        self.target = (self.x, self.y)
        self.next_move = 0
        self.next_attack = now + 1200
        self.scheduled = []  # naplánované vlny útokov: (čas, funkcia)
        self.last_attack = None
        self.phase = 1
        self.flash = 0
        self.angle = 0

    @property
    def rect(self):
        return pygame.Rect(self.x - BOSS_SIZE / 2, self.y - BOSS_SIZE / 2, BOSS_SIZE, BOSS_SIZE)

    @property
    def color(self):
        return RED if self.phase == 1 else ORANGE

    def pick_target(self):
        margin = BOSS_SIZE
        self.target = (random.uniform(ARENA.left + margin, ARENA.right - margin),
                       random.uniform(ARENA.top + margin, ARENA.top + ARENA.height * 0.6))

    def update(self, now, player):
        # Vráti True, keď boss práve prešiel do 2. fázy #
        phase_changed = False
        if self.phase == 1 and self.health <= self.max_health // 2:
            self.phase = 2
            self.scheduled.clear()
            self.next_attack = now + 1000
            phase_changed = True

        # Pohyb – boss plynulo letí k náhodne zvolenému bodu #
        speed = BOSS_VEL * (1.6 if self.phase == 2 else 1)
        dx, dy = self.target[0] - self.x, self.target[1] - self.y
        dist = math.hypot(dx, dy)
        if now >= self.next_move or dist < 4:
            self.pick_target()
            self.next_move = now + MOVE_DELAY
        else:
            step = min(speed, dist)
            self.x += dx / dist * step
            self.y += dy / dist * step

        # Naplánované vlny #
        for item in self.scheduled[:]:
            if now >= item[0]:
                self.scheduled.remove(item)
                item[1]()

        # Nový útok #
        if now >= self.next_attack and not self.scheduled:
            attacks = [self.attack_cross, self.attack_double_wave, self.attack_walls, self.attack_ring,
                       self.attack_aimed]
            if self.phase == 2:
                attacks.append(self.attack_spiral)
            if self.last_attack in attacks:
                attacks.remove(self.last_attack)
            self.last_attack = random.choice(attacks)
            self.last_attack(now, player)
            self.next_attack = now + self.attack_delay * (0.75 if self.phase == 2 else 1)

        self.flash = max(0, self.flash - 1)
        self.angle += 0.02 * self.phase
        self.shown_health += (self.health - self.shown_health) * 0.05
        return phase_changed

    def fire(self, x, y, vx, vy, delay=0, radius=9):
        self.bullets.append(Bullet(x, y, vx, vy, radius, self.color, delay))

    def fire_four_ways(self, offsets):
        v = self.bullet_vel
        half = BOSS_SIZE // 2
        for off in offsets:
            self.fire(self.x - half, self.y + off, -v, 0)
            self.fire(self.x + half, self.y + off, v, 0)
            self.fire(self.x + off, self.y - half, 0, -v)
            self.fire(self.x + off, self.y + half, 0, v)
        self.sounds.play("boss_shot")

    # Útok 1: Kríž – 5 rovnobežných striel do každej strany (pôvodný útok 1) #
    def attack_cross(self, now, player):
        self.fire_four_ways((-60, -30, 0, 30, 60))

    # Útok 2: Dvojitá vlna – najprv vonkajšie strely, potom vnútorné (pôvodné útoky 2 a 4) #
    def attack_double_wave(self, now, player):
        self.fire_four_ways((-75, -45, 45, 75))
        self.scheduled.append((now + ATTACK_WAVE_DELAY, lambda: self.fire_four_ways((-30, 0, 30))))

    # Útok 3: Steny – strely prilietajú z okrajov, najprv bliká varovanie (pôvodný útok 3) #
    def attack_walls(self, now, player):
        v = self.bullet_vel
        for off in (-150, -75, 0, 75, 150):
            y = self.y + off
            if ARENA.top < y < ARENA.bottom:
                self.fire(ARENA.right - 8, y, -v, 0, WARNING_TIME)
                self.fire(ARENA.left + 8, y, v, 0, WARNING_TIME)
            x = self.x + off
            if ARENA.left < x < ARENA.right:
                self.fire(x, ARENA.top + 8, 0, v, WARNING_TIME)
                self.fire(x, ARENA.bottom - 8, 0, -v, WARNING_TIME)
        self.sounds.play("boss_shot")

    # Útok 4: Kruh striel do všetkých strán #
    def attack_ring(self, now, player):
        def ring(count, start, speed):
            for i in range(count):
                a = start + math.tau * i / count
                self.fire(self.x, self.y, math.cos(a) * speed, math.sin(a) * speed)
            self.sounds.play("boss_shot")

        count = 16 if self.phase == 1 else 22
        start = random.uniform(0, math.tau)
        ring(count, start, self.bullet_vel)
        if self.phase == 2:
            self.scheduled.append((now + 350, lambda: ring(count, start + math.pi / count, self.bullet_vel * 0.8)))

    # Útok 5: Mierené dávky priamo na hráča #
    def attack_aimed(self, now, player):
        def volley():
            base = math.atan2(player.y - self.y, player.x - self.x)
            speed = self.bullet_vel * 1.3
            for spread in (-0.3, -0.15, 0, 0.15, 0.3):
                self.fire(self.x, self.y, math.cos(base + spread) * speed, math.sin(base + spread) * speed, radius=7)
            self.sounds.play("boss_shot")

        volley()
        for k in range(1, 3 if self.phase == 1 else 4):
            self.scheduled.append((now + 280 * k, volley))

    # Útok 6: Špirála (len v 2. fáze) #
    def attack_spiral(self, now, player):
        start = random.uniform(0, math.tau)

        def arms(step):
            for arm in range(3):
                a = start + step * 0.33 + arm * math.tau / 3
                self.fire(self.x, self.y, math.cos(a) * self.bullet_vel, math.sin(a) * self.bullet_vel, radius=7)
            if step % 3 == 0:
                self.sounds.play("boss_shot")

        for step in range(20):
            self.scheduled.append((now + step * 70, lambda step=step: arms(step)))

    def draw(self, surf, now, look_at):
        pulse = math.sin(now / 180) * 3
        color = WHITE if self.flash else self.color
        dark = DARK_RED if self.phase == 1 else DARK_ORANGE
        center = (int(self.x), int(self.y))
        blit_glow(surf, 95, color, center, 0.7)

        # Bodky obiehajúce okolo bossa #
        count = 6 if self.phase == 1 else 10
        for i in range(count):
            a = self.angle + math.tau * i / count
            pygame.draw.circle(surf, color, (int(self.x + math.cos(a) * (60 + pulse)),
                                             int(self.y + math.sin(a) * (60 + pulse))), 4)

        # Hroty v 2. fáze #
        if self.phase == 2:
            for i in range(8):
                a = -self.angle * 1.5 + math.tau * i / 8
                tip = (self.x + math.cos(a) * (56 + pulse), self.y + math.sin(a) * (56 + pulse))
                left = (self.x + math.cos(a - 0.25) * 38, self.y + math.sin(a - 0.25) * 38)
                right = (self.x + math.cos(a + 0.25) * 38, self.y + math.sin(a + 0.25) * 38)
                pygame.draw.polygon(surf, color, [tip, left, right])

        # Telo #
        size = BOSS_SIZE + pulse
        body = pygame.Rect(0, 0, size, size)
        body.center = center
        pygame.draw.rect(surf, dark, body.inflate(10, 10), border_radius=18)
        pygame.draw.rect(surf, color, body, border_radius=16)

        # Oči sledujúce hráča #
        a = math.atan2(look_at[1] - self.y, look_at[0] - self.x)
        px, py = math.cos(a) * 4, math.sin(a) * 4
        for ex in (-15, 15):
            ecx, ecy = self.x + ex, self.y - 8
            pygame.draw.ellipse(surf, WHITE, pygame.Rect(ecx - 10, ecy - 8, 20, 16))
            pygame.draw.circle(surf, BLACK, (int(ecx + px), int(ecy + py)), 5)
        pygame.draw.line(surf, dark, (self.x - 27, self.y - 23), (self.x - 6, self.y - 15), 4)
        pygame.draw.line(surf, dark, (self.x + 27, self.y - 23), (self.x + 6, self.y - 15), 4)

        # Zubatá pusa #
        mouth = [(self.x - 18 + i * 6, self.y + 14 + (5 if i % 2 else 0)) for i in range(7)]
        pygame.draw.lines(surf, dark, False, mouth, 3)

# # # HRA # # #

class Game:
    def __init__(self):
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.sounds = Sounds()
        self.background = Background()
        self.highscores = load_highscores()
        self.difficulty = 1
        self.state = "menu"
        self.running = True
        self.menu_index = 0
        self.pause_index = 0
        self.menu_rects = []
        self.shake = 0
        self.menu_boss = Boss(DIFFICULTIES[1], [], self.sounds)
        self.new_game()
        self.state = "menu"

    # Príprava novej hry #

    def new_game(self):
        diff = DIFFICULTIES[self.difficulty]
        self.game_time = 0
        self.player_bullets = []
        self.boss_bullets = []
        self.particles = []
        self.texts = []
        self.player = Player(diff["player_health"])
        self.boss = Boss(diff, self.boss_bullets, self.sounds)
        self.stats = {"kill": 0, "hit": 0, "miss": 0, "hurt": 0}
        self.ending = False
        self.won = False
        self.end_time = 0
        self.hurt_flash = 0
        self.banner = None
        self.final_score = 0
        self.new_record = False
        self.state = "countdown"
        self.state_start = pygame.time.get_ticks()

    # Hlavná slučka #

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS), 50)
            self.step(dt, pygame.event.get())
        pygame.quit()

    def step(self, dt, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                self.sounds.toggle()
        getattr(self, "state_" + self.state)(dt, events)

        # Trasenie obrazovky #
        offset = (0, 0)
        if self.shake > 0.5:
            offset = (random.uniform(-self.shake, self.shake), random.uniform(-self.shake, self.shake))
            self.shake *= 0.88
        else:
            self.shake = 0
        WIN.fill(BLACK)
        WIN.blit(self.canvas, offset)
        pygame.display.flip()

    # Ovládanie menu (klávesnica aj myš) #

    def menu_input(self, events, count, index):
        activated, delta = None, 0
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_w, pygame.K_UP):
                    index = (index - 1) % count
                    self.sounds.play("move")
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    index = (index + 1) % count
                    self.sounds.play("move")
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    activated = index
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    delta = -1
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    delta = 1
            elif event.type == pygame.MOUSEMOTION:
                for i, rect in enumerate(self.menu_rects[:count]):
                    if rect.collidepoint(event.pos) and i != index:
                        index = i
                        self.sounds.play("move")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(self.menu_rects[:count]):
                    if rect.collidepoint(event.pos):
                        index, activated = i, i
        if activated is not None:
            self.sounds.play("select")
        return index, activated, delta

    def draw_menu_items(self, items, index, top):
        self.menu_rects = []
        now = pygame.time.get_ticks()
        for i, label in enumerate(items):
            rect = pygame.Rect(0, 0, 420, 48)
            rect.center = (WIDTH // 2, top + i * 60)
            if i == index:
                grow = int(math.sin(now / 150) * 3)
                highlight = pygame.Surface(rect.inflate(grow * 2, 0).size, pygame.SRCALPHA)
                pygame.draw.rect(highlight, (*GOLD, 45), highlight.get_rect(), border_radius=12)
                pygame.draw.rect(highlight, (*GOLD, 200), highlight.get_rect(), 2, border_radius=12)
                self.canvas.blit(highlight, highlight.get_rect(center=rect.center))
                draw_text(self.canvas, label, FONT, GOLD, rect.center)
            else:
                draw_text(self.canvas, label, FONT, GREY, rect.center)
            self.menu_rects.append(rect)

    def draw_title(self, text, y, color=GOLD, font=FONT_HUGE):
        blit_glow(self.canvas, 160, tuple(c // 3 for c in color), (WIDTH // 2, y), 0.8)
        draw_text(self.canvas, text, font, color, (WIDTH // 2, y))

    def draw_overlay(self, alpha=170):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 5, 15, alpha))
        self.canvas.blit(overlay, (0, 0))

    # Stav: hlavné menu #

    def state_menu(self, dt, events):
        items = ["Hrať",
                 "Obtiažnosť:  < " + DIFFICULTIES[self.difficulty]["name"] + " >",
                 "Ovládanie",
                 "Zvuk:  " + ("zapnutý" if self.sounds.enabled else "vypnutý"),
                 "Koniec"]
        self.menu_index, activated, delta = self.menu_input(events, len(items), self.menu_index)
        if self.menu_index == 1 and delta:
            self.difficulty = (self.difficulty + delta) % len(DIFFICULTIES)
            self.sounds.play("move")
        if activated == 0:
            self.new_game()
        elif activated == 1:
            self.difficulty = (self.difficulty + 1) % len(DIFFICULTIES)
        elif activated == 2:
            self.state = "controls"
        elif activated == 3:
            self.sounds.toggle()
        elif activated == 4:
            self.running = False

        now = pygame.time.get_ticks()
        self.background.update()
        self.background.draw(self.canvas)
        boss = self.menu_boss
        boss.x, boss.y = WIDTH // 2, 235 + math.sin(now / 500) * 8
        boss.angle += 0.02
        boss.draw(self.canvas, now, pygame.mouse.get_pos())
        self.draw_title("POSLEDNÝ STRÁŽCA", 85 + math.sin(now / 700) * 4)
        draw_text(self.canvas, "Hra na ročníkovú prácu", FONT_SMALL, GREY, (WIDTH // 2, 145))
        self.draw_menu_items(items, self.menu_index, 335)

        name = DIFFICULTIES[self.difficulty]["name"]
        best = self.highscores.get(name, 0)
        draw_text(self.canvas, f"Najlepšie skóre ({name}): {best}", FONT_SMALL, GOLD, (WIDTH // 2, 640))
        draw_text(self.canvas, "W/S alebo šípky – výber     Enter – potvrdiť", FONT_SMALL, GREY, (WIDTH // 2, 672))

    # Stav: ovládanie #

    def state_controls(self, dt, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.state = "menu"
                self.sounds.play("select")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.state = "menu"

        self.background.update()
        self.background.draw(self.canvas)
        self.draw_title("OVLÁDANIE", 80, CYAN, FONT_BIG)
        panel = pygame.Rect(0, 0, 720, 470)
        panel.center = (WIDTH // 2, 380)
        box = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(box, (20, 16, 45, 220), box.get_rect(), border_radius=16)
        pygame.draw.rect(box, (*ARENA_BORDER, 255), box.get_rect(), 2, border_radius=16)
        self.canvas.blit(box, panel)

        rows = [("W A S D", "pohyb"),
                ("Šípky", "streľba (aj šikmo)"),
                ("Medzerník", "úskok – počas neho si nezraniteľný"),
                ("ESC / P", "pauza"),
                ("M", "zvuk zapnúť / vypnúť")]
        for i, (key, action) in enumerate(rows):
            y = panel.top + 45 + i * 45
            draw_text(self.canvas, key, FONT, GOLD, (panel.left + 200, y), "midright")
            draw_text(self.canvas, action, FONT, WHITE, (panel.left + 230, y), "midleft")

        tips = ["Trafená strela +50, netrafená −10, zranenie −100, výhra +500.",
                "Pri streľbe ťa spätný ráz trochu odtlačí.",
                "Blikajúce krúžky na okrajoch = o chvíľu odtiaľ priletia strely.",
                "V polovici životov prejde boss do 2. fázy a pritvrdí!"]
        for i, tip in enumerate(tips):
            draw_text(self.canvas, tip, FONT_SMALL, GREY, (WIDTH // 2, panel.top + 290 + i * 34))
        draw_text(self.canvas, "ESC / Enter – späť", FONT_SMALL, GOLD, (WIDTH // 2, 660))

    # Stav: odpočet pred hrou #

    def state_countdown(self, dt, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = "menu"
                return
        elapsed = pygame.time.get_ticks() - self.state_start
        self.background.update()
        self.draw_scene()
        step = elapsed // 700
        if step >= 4:
            self.state = "play"
            return
        text = ["3", "2", "1", "Začiatok hry!"][step]
        scale = 1 + (1 - (elapsed % 700) / 700) * 0.5
        image = (FONT_HUGE if step < 3 else FONT_BIG).render(text, True, GOLD)
        image = pygame.transform.rotozoom(image, 0, scale)
        blit_glow(self.canvas, 140, (80, 60, 20), (WIDTH // 2, HEIGHT // 2), 0.8)
        self.canvas.blit(image, image.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    # Stav: samotná hra #

    def state_play(self, dt, events):
        keys = pygame.key.get_pressed()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p) and not self.ending:
                    self.state = "pause"
                    self.pause_index = 0
                    self.sounds.play("select")
                elif event.key == pygame.K_SPACE and not self.ending:
                    if self.player.try_dash(keys, self.game_time):
                        self.sounds.play("dash")
        if self.state != "play":
            self.draw_scene()
            return

        self.game_time += dt
        now = self.game_time
        player, boss = self.player, self.boss

        if not self.ending:
            player.update(keys, now)
            bullet = player.try_shoot(keys, now)
            if bullet:
                self.player_bullets.append(bullet)
                self.sounds.play("shoot")
            if boss.update(now, player):
                self.on_phase_two()

        # Strely hráča #
        for bullet in self.player_bullets[:]:
            bullet.update(dt)
            if boss.health > 0 and circle_hits_rect(bullet.x, bullet.y, bullet.radius, boss.rect):
                self.player_bullets.remove(bullet)
                self.on_boss_hit(bullet)
            elif bullet.outside(ARENA):
                self.player_bullets.remove(bullet)
                burst(self.particles, bullet.x, bullet.y, 4, [CYAN], 2, 15, 3)
                if not self.ending:
                    self.stats["miss"] += MISS_SCORE

        # Strely nepriateľa #
        for bullet in self.boss_bullets[:]:
            bullet.update(dt)
            if not bullet.active:
                continue
            if bullet.outside(ARENA, 30):
                self.boss_bullets.remove(bullet)
            elif (not self.ending and not player.is_invincible(now)
                  and circle_hits_rect(bullet.x, bullet.y, bullet.radius, player.hitbox)):
                self.boss_bullets.remove(bullet)
                self.on_player_hit()

        # Dotyk s bossom tiež zraňuje #
        if (not self.ending and not player.is_invincible(now)
                and player.hitbox.colliderect(boss.rect.inflate(-10, -10))):
            self.on_player_hit()

        self.update_effects()
        self.background.update(2 if boss.phase == 2 else 1)

        # Koniec hry #
        if not self.ending:
            if boss.health <= 0:
                self.start_ending(True)
            elif player.health <= 0:
                self.start_ending(False)
        elif now >= self.end_time:
            self.finish_game()

        self.draw_scene()

    def update_effects(self):
        for particle in self.particles:
            particle.update()
        self.particles = [p for p in self.particles if p.life > 0]
        for text in self.texts:
            text.update()
        self.texts = [t for t in self.texts if t.life > 0]
        self.hurt_flash = max(0, self.hurt_flash - 1)

    # Udalosti v hre #

    def on_boss_hit(self, bullet):
        self.boss.health -= 1
        self.boss.flash = 4
        self.stats["hit"] += HIT_SCORE
        burst(self.particles, bullet.x, bullet.y, 8, [LIGHT_CYAN, self.boss.color, WHITE], 4, 25, 3)
        self.texts.append(FloatingText(bullet.x, bullet.y - 10, f"+{HIT_SCORE}", GOLD))
        self.sounds.play("hit")
        self.shake = max(self.shake, 2)

    def on_player_hit(self):
        player = self.player
        player.health -= 1
        player.invincible_until = self.game_time + I_FRAMES
        self.stats["hurt"] += HURT_SCORE
        burst(self.particles, player.x, player.y, 20, [CYAN, PINK, WHITE], 5, 35, 4)
        self.texts.append(FloatingText(player.x, player.y - 25, str(HURT_SCORE), RED))
        self.sounds.play("hurt")
        self.shake = 12
        self.hurt_flash = 14

    def on_phase_two(self):
        self.banner = ("FÁZA 2!", self.game_time + 1800)
        self.shake = 18
        burst(self.particles, self.boss.x, self.boss.y, 60, [ORANGE, GOLD, RED], 8, 50, 5)
        self.sounds.play("phase")

    def start_ending(self, won):
        self.ending = True
        self.won = won
        self.end_time = self.game_time + END_DELAY
        self.shake = 25
        self.sounds.play("explode")
        if won:
            self.stats["kill"] = KILL_SCORE
            self.boss.scheduled.clear()
            burst(self.particles, self.boss.x, self.boss.y, 150, [RED, ORANGE, GOLD, WHITE], 9, 80, 7)
            for bullet in self.boss_bullets:
                burst(self.particles, bullet.x, bullet.y, 3, [bullet.color], 2, 20, 3)
            self.boss_bullets.clear()
        else:
            burst(self.particles, self.player.x, self.player.y, 90, [CYAN, LIGHT_CYAN, WHITE], 7, 70, 5)

    def finish_game(self):
        score = sum(self.stats.values())
        self.final_score = max(0, round(score * DIFFICULTIES[self.difficulty]["mult"]))
        name = DIFFICULTIES[self.difficulty]["name"]
        self.new_record = self.final_score > self.highscores.get(name, 0)
        if self.new_record:
            self.highscores[name] = self.final_score
            save_highscores(self.highscores)
        self.state = "game_over"
        self.state_start = pygame.time.get_ticks()
        self.pause_index = 0
        self.menu_rects = []

    # Vykreslenie hry #

    def draw_scene(self):
        c = self.canvas
        now = self.game_time
        self.background.draw(c)
        pygame.draw.rect(c, ARENA_BORDER, ARENA, 2, border_radius=6)

        if not (self.ending and self.won):
            self.boss.draw(c, now, (self.player.x, self.player.y))
        if not (self.ending and not self.won):
            self.player.draw(c, now)
        for bullet in self.player_bullets:
            bullet.draw(c, now)
        for bullet in self.boss_bullets:
            bullet.draw(c, now)
        for particle in self.particles:
            particle.draw(c)
        for text in self.texts:
            text.draw(c)

        if self.hurt_flash:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 0, 40, self.hurt_flash * 6))
            c.blit(flash, (0, 0))

        if self.banner and now < self.banner[1]:
            draw_text(c, self.banner[0], FONT_HUGE, ORANGE, (WIDTH // 2, HEIGHT // 2 - 40))

        self.draw_hud()

    def draw_hud(self):
        c = self.canvas
        player, boss = self.player, self.boss

        # Životy hráča #
        draw_text(c, "Životy", FONT_SMALL, WHITE, (22, 20), "midleft")
        for i in range(player.max_health):
            draw_heart(c, 100 + i * 28, 22, 22, PINK if i < player.health else (60, 50, 80))

        # Životy nepriateľa #
        bar = pygame.Rect(0, 0, 400, 16)
        bar.center = (WIDTH // 2, 45)
        draw_text(c, "STRÁŽCA", FONT_SMALL, boss.color, (WIDTH // 2, 20))
        pygame.draw.rect(c, DARK, bar.inflate(6, 6), border_radius=6)
        shown = max(0, boss.shown_health / boss.max_health)
        real = max(0, boss.health / boss.max_health)
        pygame.draw.rect(c, WHITE, (bar.left, bar.top, bar.width * shown, bar.height), border_radius=4)
        pygame.draw.rect(c, boss.color, (bar.left, bar.top, bar.width * real, bar.height), border_radius=4)
        pygame.draw.line(c, GREY, (bar.centerx, bar.top - 2), (bar.centerx, bar.bottom + 2), 2)
        pygame.draw.rect(c, GREY, bar.inflate(6, 6), 2, border_radius=6)

        # Skóre #
        score = sum(self.stats.values())
        draw_text(c, f"Skóre: {score}", FONT, GOLD, (WIDTH - 22, 30), "midright")

        # Úskok a spodná lišta #
        ready = min(1, 1 - (player.next_dash - self.game_time) / DASH_COOLDOWN)
        draw_text(c, "Úskok", FONT_SMALL, WHITE, (22, HEIGHT - 20), "midleft")
        dash_bar = pygame.Rect(90, HEIGHT - 27, 120, 14)
        pygame.draw.rect(c, DARK, dash_bar, border_radius=5)
        pygame.draw.rect(c, CYAN if ready >= 1 else DARK_CYAN,
                         (dash_bar.left, dash_bar.top, dash_bar.width * max(0, ready), dash_bar.height),
                         border_radius=5)
        pygame.draw.rect(c, GREY, dash_bar, 2, border_radius=5)
        draw_text(c, "Obtiažnosť: " + DIFFICULTIES[self.difficulty]["name"], FONT_SMALL, GREY,
                  (WIDTH // 2, HEIGHT - 20))
        draw_text(c, "ESC – pauza", FONT_SMALL, GREY, (WIDTH - 22, HEIGHT - 20), "midright")

    # Stav: pauza #

    def state_pause(self, dt, events):
        items = ["Pokračovať", "Začať odznova", "Hlavné menu"]
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
                self.state = "play"
                return
        self.pause_index, activated, _ = self.menu_input(events, len(items), self.pause_index)
        if activated == 0:
            self.state = "play"
        elif activated == 1:
            self.new_game()
        elif activated == 2:
            self.state = "menu"
        self.draw_scene()
        self.draw_overlay()
        self.draw_title("PAUZA", 200, CYAN, FONT_HUGE)
        self.draw_menu_items(items, self.pause_index, 360)

    # Stav: koniec hry #

    def state_game_over(self, dt, events):
        items = ["Hrať znova", "Hlavné menu"]
        self.pause_index, activated, _ = self.menu_input(events, len(items), self.pause_index)
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                activated = 1
        if activated == 0:
            self.new_game()
            return
        if activated == 1:
            self.state = "menu"
            return

        self.update_effects()
        self.background.update()
        self.draw_scene()
        self.draw_overlay(190)

        if self.won:
            self.draw_title("Vyhral si!", 90, GREEN)
        else:
            self.draw_title("Prehral si!", 90, RED)

        # Riadky sa objavujú postupne #
        elapsed = pygame.time.get_ticks() - self.state_start
        mult = DIFFICULTIES[self.difficulty]["mult"]
        name = DIFFICULTIES[self.difficulty]["name"]
        rows = [("Nepriateľ zabitý", str(self.stats["kill"]), WHITE),
                ("Strely trafené", str(self.stats["hit"]), WHITE),
                ("Strely netrafené", str(self.stats["miss"]), WHITE),
                ("Počet zranení", str(self.stats["hurt"]), WHITE),
                ("Násobič obtiažnosti", f"x{mult}", WHITE),
                ("Finálne skóre", str(self.final_score), GOLD),
                (f"Najlepšie skóre ({name})", str(self.highscores.get(name, 0)), GREY)]
        for i, (label, value, color) in enumerate(rows):
            if elapsed < 250 * (i + 1):
                break
            y = 175 + i * 42 + (15 if i >= 5 else 0)
            font = FONT_BIG if i == 5 else FONT
            draw_text(self.canvas, label, font, color, (WIDTH // 2 - 290, y), "midleft")
            draw_text(self.canvas, value, font, color, (WIDTH // 2 + 290, y), "midright")
            if i == 4:
                pygame.draw.line(self.canvas, GREY, (WIDTH // 2 - 290, y + 24), (WIDTH // 2 + 290, y + 24), 2)

        if self.new_record and elapsed > 250 * len(rows) and (pygame.time.get_ticks() // 300) % 2:
            draw_text(self.canvas, "NOVÝ REKORD!", FONT_BIG, GOLD, (WIDTH // 2, 500))

        if elapsed > 250 * len(rows):
            self.draw_menu_items(items, self.pause_index, 570)

# # # SPUSTENIE HRY # # #

if __name__ == "__main__":
    Game().run()
