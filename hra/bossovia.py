# # # BOSSOVIA # # #
# Každá kazeta má vlastného bossa. Spoločné správanie je v triede Boss, #
# jednotliví bossovia si vyberajú útoky a pridávajú vlastné schopnosti.  #

import math
import random

import pygame

from grafika import blit_glow, dim, make_sprite
from nastavenia import *
from strely import Bullet


class Boss:
    name = "BOSS"
    sprites = []        # snímky animácie (textové obrázky)
    palettes = []       # farby pre každú fázu
    anim = [{}]         # zmeny farieb pre jednotlivé snímky animácie
    scale = 5
    hp_mult = 1.0
    phase_marks = (0.5,)  # pri akom podiele životov začne ďalšia fáza
    colors = (RED, ORANGE)
    move_speed = 2.2
    frame_time = 250

    def __init__(self, difficulty, bullets, sounds, player):
        self.bullets = bullets
        self.sounds = sounds
        self.player = player
        self.health = self.max_health = round(difficulty["boss_health"] * self.hp_mult)
        self.shown_health = float(self.health)  # pomaly klesajúci pásik životov
        self.bullet_vel = difficulty["bullet_vel"]
        self.attack_delay = difficulty["attack_delay"]

        count = max(len(self.sprites), len(self.anim))
        self.frames = [[make_sprite(self.sprites[i % len(self.sprites)], {**palette, **self.anim[i % len(self.anim)]},
                                    self.scale) for i in range(count)]
                       for palette in self.palettes]
        self.flash_frame = make_sprite(self.sprites[0], {ch: WHITE for ch in self.palettes[0]}, self.scale)
        self.width, self.height = self.flash_frame.get_size()

        self.x = ARENA.centerx
        self.y = ARENA.top + 130
        self.target = (self.x, self.y)
        self.next_move = 0
        self.next_attack = 1200
        self.scheduled = []  # naplánované vlny útokov: (čas, funkcia)
        self.last_attack = None
        self.phase = 1
        self.flash = 0
        self.angle = 0
        self.alpha = 255
        self.invulnerable = False
        self.shake_request = 0  # o koľko má hra zatriasť obrazovkou
        self.osd = None         # nápis v štýle VHS (napr. REW) a dokedy svieti

    @property
    def rect(self):
        r = pygame.Rect(0, 0, self.width * 0.8, self.height * 0.8)
        r.center = (self.x, self.y)
        return r

    @property
    def color(self):
        return self.colors[self.phase - 1]

    def phase_for_health(self):
        phase = 1
        for mark in self.phase_marks:
            if self.health <= self.max_health * mark:
                phase += 1
        return phase

    # Pohyb #

    def pick_target(self):
        mx, my = self.width, self.height
        self.target = (random.uniform(ARENA.left + mx, ARENA.right - mx),
                       random.uniform(ARENA.top + my, ARENA.top + ARENA.height * 0.6))

    def move(self, now):
        speed = self.move_speed * (1 + 0.3 * (self.phase - 1))
        dx, dy = self.target[0] - self.x, self.target[1] - self.y
        dist = math.hypot(dx, dy)
        if now >= self.next_move or dist < 4:
            self.pick_target()
            self.next_move = now + MOVE_DELAY
        else:
            step = min(speed, dist)
            self.x += dx / dist * step
            self.y += dy / dist * step

    # Hlavná aktualizácia – vráti True, keď boss prešiel do ďalšej fázy #

    def attacks(self):
        return [self.attack_cross]

    def busy(self):
        return bool(self.scheduled)

    def update(self, now):
        phase_changed = False
        new_phase = self.phase_for_health()
        if new_phase > self.phase:
            self.phase = new_phase
            self.scheduled.clear()
            self.next_attack = now + 1000
            phase_changed = True

        self.move(now)

        for item in self.scheduled[:]:
            if now >= item[0]:
                self.scheduled.remove(item)
                item[1]()

        if now >= self.next_attack and not self.busy():
            attacks = self.attacks()
            if self.last_attack in attacks and len(attacks) > 1:
                attacks.remove(self.last_attack)
            self.last_attack = random.choice(attacks)
            self.last_attack(now)
            self.next_attack = now + self.attack_delay * (1 - 0.15 * (self.phase - 1))

        self.flash = max(0, self.flash - 1)
        self.angle += 0.02 * self.phase
        self.shown_health += (self.health - self.shown_health) * 0.05
        return phase_changed

    # # # KNIŽNICA ÚTOKOV # # #

    def later(self, time, action):
        self.scheduled.append((time, action))

    def fire(self, x, y, vx, vy, delay=0, radius=9, **extra):
        self.bullets.append(Bullet(x, y, vx, vy, radius, self.color, delay, **extra))

    def fire_four_ways(self, offsets):
        v = self.bullet_vel
        hw, hh = self.width // 2, self.height // 2
        for off in offsets:
            self.fire(self.x - hw, self.y + off, -v, 0)
            self.fire(self.x + hw, self.y + off, v, 0)
            self.fire(self.x + off, self.y - hh, 0, -v)
            self.fire(self.x + off, self.y + hh, 0, v)
        self.sounds.play("boss_shot")

    def ring(self, count, start, speed, radius=9, **extra):
        for i in range(count):
            a = start + math.tau * i / count
            self.fire(self.x, self.y, math.cos(a) * speed, math.sin(a) * speed, radius=radius, **extra)
        self.sounds.play("boss_shot")

    def laser(self, now, x=None, y=None):
        # Najprv bodkovaná čiara (varovanie), potom na chvíľu zasvieti laser #
        if x is not None:
            for yy in range(ARENA.top + 8, ARENA.bottom, 16):
                self.fire(x, yy, 0, 0, LASER_WARNING, radius=7, life=LASER_TIME)
        if y is not None:
            for xx in range(ARENA.left + 8, ARENA.right, 16):
                self.fire(xx, y, 0, 0, LASER_WARNING, radius=7, life=LASER_TIME)
        self.later(now + LASER_WARNING, lambda: self.sounds.play("laser"))

    # Kríž – 5 rovnobežných striel do každej strany (pôvodný útok 1) #
    def attack_cross(self, now):
        self.fire_four_ways((-60, -30, 0, 30, 60))

    # Dvojitá vlna – najprv vonkajšie strely, potom vnútorné (pôvodné útoky 2 a 4) #
    def attack_double_wave(self, now):
        self.fire_four_ways((-75, -45, 45, 75))
        self.later(now + ATTACK_WAVE_DELAY, lambda: self.fire_four_ways((-30, 0, 30)))

    # Steny – strely prilietajú z okrajov, najprv bliká varovanie (pôvodný útok 3) #
    def attack_walls(self, now):
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

    # Kruh striel do všetkých strán #
    def attack_ring(self, now):
        count = 12 + 5 * self.phase
        start = random.uniform(0, math.tau)
        self.ring(count, start, self.bullet_vel)
        if self.phase >= 2:
            self.later(now + 350, lambda: self.ring(count, start + math.pi / count, self.bullet_vel * 0.8))

    # Mierené dávky priamo na hráča #
    def attack_aimed(self, now):
        def volley():
            base = math.atan2(self.player.y - self.y, self.player.x - self.x)
            speed = self.bullet_vel * 1.3
            for spread in (-0.3, -0.15, 0, 0.15, 0.3):
                self.fire(self.x, self.y, math.cos(base + spread) * speed, math.sin(base + spread) * speed, radius=7)
            self.sounds.play("boss_shot")

        volley()
        for k in range(1, 2 + self.phase):
            self.later(now + 280 * k, volley)

    # Špirála #
    def attack_spiral(self, now):
        start = random.uniform(0, math.tau)
        arms = 2 + self.phase

        def shoot(step):
            for arm in range(arms):
                a = start + step * 0.33 + arm * math.tau / arms
                self.fire(self.x, self.y, math.cos(a) * self.bullet_vel, math.sin(a) * self.bullet_vel, radius=7)
            if step % 3 == 0:
                self.sounds.play("boss_shot")

        for step in range(20):
            self.later(now + step * 70, lambda step=step: shoot(step))

    # Dážď striel zhora #
    def attack_rain(self, now):
        for i in range(10 + 4 * self.phase):
            x = random.uniform(ARENA.left + 15, ARENA.right - 15)
            self.fire(x, ARENA.top + 8, random.uniform(-0.4, 0.4), self.bullet_vel * 1.1,
                      WARNING_TIME + i * 60, radius=7)

    # Navádzané gule #
    def attack_homing(self, now):
        count = 3 + self.phase
        for i in range(count):
            a = math.tau * i / count + self.angle
            self.fire(self.x, self.y, math.cos(a) * self.bullet_vel * 0.9, math.sin(a) * self.bullet_vel * 0.9,
                      radius=10, homing=0.035, homing_frames=100)
        self.sounds.play("boss_shot")

    # Laser tam, kde práve stojí hráč #
    def attack_laser_cross(self, now):
        self.laser(now, x=self.player.x, y=self.player.y)
        if self.phase >= 2:
            self.later(now + 600, lambda: self.laser(now + 600, x=self.player.x + random.choice((-90, 90))))

    # Nakreslenie #

    def draw(self, surf, now):
        frames = self.frames[self.phase - 1]
        image = self.flash_frame if self.flash else frames[(now // self.frame_time) % len(frames)]
        x = self.x
        y = self.y + math.sin(now / 300) * 4
        if self.alpha < 255:
            image = image.copy()
            image.set_alpha(self.alpha)
        else:
            blit_glow(surf, max(self.width, self.height) * 0.95, dim(self.color, 0.6), (int(x), int(y)), 0.8)
            count = 4 + 2 * self.phase
            orbit = max(self.width, self.height) * 0.75
            for i in range(count):
                a = self.angle + math.tau * i / count
                surf.fill(self.color, (int(x + math.cos(a) * orbit) - 3, int(y + math.sin(a) * orbit) - 3, 6, 6))
        surf.blit(image, image.get_rect(center=(int(x), int(y))))

# # # 1. KAZETA: STRÁŽCA # # #

class Guardian(Boss):
    name = "STRÁŽCA"
    sprites = [[
        "..kkkkkkkkkk..",
        ".klllaaaaaaak.",
        "kllaaaaaaaaadk",
        "kladdaaaaddadk",
        "klaaddaaddaadk",
        "kawwwaaaawwwdk",
        "kawweaaaaewwdk",
        "kawwwaaaawwwdk",
        "kaaaaaaaaaaadk",
        "kaakkkkkkkkadk",
        "kaakwkwkwkkadk",
        "kaaakkkkkkaadk",
        ".kddddddddddk.",
        "..kkkkkkkkkk..",
    ]]
    palettes = [
        {"k": (40, 8, 20), "a": RED, "d": (160, 30, 60), "l": (255, 150, 170), "w": WHITE, "e": BLACK},
        {"k": (50, 20, 5), "a": ORANGE, "d": (170, 80, 20), "l": (255, 210, 150), "w": WHITE, "e": BLACK},
    ]
    colors = (RED, ORANGE)
    hp_mult = 1.0

    def attacks(self):
        attacks = [self.attack_cross, self.attack_double_wave, self.attack_walls, self.attack_ring, self.attack_aimed]
        if self.phase >= 2:
            attacks.append(self.attack_spiral)
        return attacks

# # # 2. KAZETA: VETRELEC # # #

class Ufo(Boss):
    name = "VETRELEC"
    sprites = [[
        "......kkkkkk......",
        ".....kggnnggk.....",
        "....kgnnnnnngk....",
        "....kgnennengk....",
        "...kkkkkkkkkkkk...",
        ".kssssssssssssssk.",
        "ksLssLssLssLssLssk",
        ".kddddddddddddddk.",
        "...kkkkkkkkkkkk...",
        ".....kyk..kyk.....",
        "......y....y......",
    ]]
    palettes = [
        {"k": (10, 30, 20), "g": (150, 230, 255), "n": GREEN, "e": BLACK, "s": (180, 190, 210),
         "d": (90, 100, 130), "L": GOLD, "y": ORANGE},
        {"k": (30, 10, 30), "g": (255, 190, 255), "n": LIME, "e": RED, "s": (200, 180, 210),
         "d": (110, 80, 130), "L": RED, "y": MAGENTA},
    ]
    anim = [{}, {"L": WHITE, "y": None}]
    colors = (GREEN, MAGENTA)
    hp_mult = 1.5
    move_speed = 3.0

    def pick_target(self):
        self.target = (random.uniform(ARENA.left + self.width, ARENA.right - self.width),
                       random.uniform(ARENA.top + self.height, ARENA.top + ARENA.height * 0.3))

    # Ťažný lúč – laser zhora na miesto hráča #
    def attack_beam(self, now):
        self.laser(now, x=self.player.x)
        if self.phase >= 2:
            self.later(now + 450, lambda: self.laser(now + 450, x=self.player.x + random.choice((-80, 80))))

    # Vejár striel, ktorý prejde zľava doprava #
    def attack_sweep(self, now):
        start, end = 0.35, math.pi - 0.35
        if random.random() < 0.5:
            start, end = end, start
        speed = self.bullet_vel * 1.2

        def shoot(a):
            self.fire(self.x, self.y, math.cos(a) * speed, math.sin(a) * speed, radius=7)
            self.fire(self.x, self.y, math.cos(a + 0.5) * speed * 0.8, math.sin(a + 0.5) * speed * 0.8, radius=7)

        for step in range(16):
            a = start + (end - start) * step / 15
            self.later(now + step * 60, lambda a=a: shoot(a))
        self.sounds.play("boss_shot")

    def attacks(self):
        attacks = [self.attack_rain, self.attack_beam, self.attack_aimed, self.attack_ring]
        if self.phase >= 2:
            attacks += [self.attack_sweep, self.attack_homing]
        return attacks

# # # 3. KAZETA: STRAŠIDLO # # #

GHOST_BODY = [
    "....kkkkkk....",
    "..kkwwwwwwkk..",
    ".kwwwwwwwwwwk.",
    ".kwwwwwwwwwwk.",
    "kwwkkwwwwkkwwk",
    "kwwkkwwwwkkwwk",
    "kwwwwwwwwwwwwk",
    "kwwwwwkkwwwwwk",
    "kwwwwkppkwwwwk",
    "kwwwwwkkwwwwwk",
    "kwwwwwwwwwwwwk",
    "kwwwwwwwwwwwwk",
    "kwwwwwwwwwwwwk",
]


class Ghost(Boss):
    name = "STRAŠIDLO"
    sprites = [
        GHOST_BODY + ["kwwk.kwwk.kwwk", ".kk...kk...kk."],
        GHOST_BODY + ["kk.kwwk.kwwk.k", "....kk...kk..."],
    ]
    palettes = [
        {"k": (70, 40, 110), "w": (235, 225, 255), "p": (40, 10, 60)},
        {"k": (20, 90, 80), "w": (190, 255, 235), "p": (10, 40, 40)},
    ]
    colors = (LILAC, TEAL)
    hp_mult = 1.9
    move_speed = 1.6
    frame_time = 300

    def __init__(self, *args):
        super().__init__(*args)
        self.fading = False
        self.fade_start = 0
        self.appear_start = -1000

    def busy(self):
        return super().busy() or self.fading

    def update(self, now):
        changed = super().update(now)
        if self.fading:
            self.alpha = max(0, int(255 - (now - self.fade_start) / 450 * 255))
        else:
            self.alpha = min(255, int(255 * (now - self.appear_start) / 250))
        return changed

    # Zmizne a objaví sa inde #
    def attack_teleport(self, now):
        self.fading = True
        self.invulnerable = True
        self.fade_start = now
        self.sounds.play("teleport")
        self.later(now + 500, lambda: self.reappear(now + 500))

    def reappear(self, now):
        for _ in range(30):
            x = random.uniform(ARENA.left + self.width, ARENA.right - self.width)
            y = random.uniform(ARENA.top + self.height, ARENA.bottom - self.height)
            if math.hypot(x - self.player.x, y - self.player.y) > 260:
                break
        self.x, self.y = x, y
        self.target = (x, y)
        self.fading = False
        self.invulnerable = False
        self.appear_start = now
        self.ring(10 + 4 * self.phase, random.uniform(0, math.tau), self.bullet_vel * 0.9)

    # Stena striel s jednou medzerou, cez ktorú treba prekĺznuť #
    def attack_curtain(self, now):
        v = self.bullet_vel * 0.9
        from_left = random.random() < 0.5
        x = ARENA.left + 8 if from_left else ARENA.right - 8
        gap = random.uniform(ARENA.top + 80, ARENA.bottom - 80)
        for y in range(ARENA.top + 10, ARENA.bottom, 24):
            if abs(y - gap) > 55:
                self.fire(x, y, v if from_left else -v, 0, WARNING_TIME, radius=8)
        self.sounds.play("boss_shot")

    def attacks(self):
        attacks = [self.attack_teleport, self.attack_homing, self.attack_curtain, self.attack_aimed]
        if self.phase >= 2:
            attacks += [self.attack_spiral, self.attack_teleport]
        return attacks

# # # 4. KAZETA: MECHA-9 # # #

class Robot(Boss):
    name = "MECHA-9"
    sprites = [[
        ".......yy.......",
        ".......kk.......",
        "..kkkkkkkkkkkk..",
        ".ksllllllllllsk.",
        ".kssssssssssssk.",
        "kkskkkkkkkkkkskk",
        "kskvvvvvvvvvvksk",
        "kskvVVvvvvVVvksk",
        "kskvvvvvvvvvvksk",
        "kkskkkkkkkkkkskk",
        ".kssssssssssssk.",
        ".ksdkdkdkdkdksk.",
        ".kssssssssssssk.",
        "..kddddddddddk..",
        "...kkkkkkkkkk...",
    ]]
    palettes = [
        {"k": (25, 25, 35), "s": (150, 160, 180), "l": (220, 225, 240), "d": (80, 85, 105),
         "v": (140, 60, 10), "V": ORANGE, "y": RED},
        {"k": (35, 15, 20), "s": (170, 140, 150), "l": (240, 210, 215), "d": (100, 60, 70),
         "v": (140, 10, 30), "V": RED, "y": RED},
    ]
    anim = [{}, {"y": (90, 20, 20)}]
    colors = (ORANGE, RED)
    hp_mult = 2.4
    move_speed = 2.6

    def __init__(self, *args):
        super().__init__(*args)
        self.telegraph = False
        self.charging = False
        self.charge_target = (0, 0)
        self.charge_start = 0

    def busy(self):
        return super().busy() or self.telegraph or self.charging

    def move(self, now):
        if self.telegraph:
            if now >= self.charge_start:
                self.telegraph = False
                self.charging = True
                dx, dy = self.charge_target[0] - self.x, self.charge_target[1] - self.y
                dist = max(1, math.hypot(dx, dy))
                self.charge_v = (dx / dist * 13, dy / dist * 13)
                self.charge_frames = int(dist / 13) + 1
                self.sounds.play("dash")
            return
        if self.charging:
            self.x += self.charge_v[0]
            self.y += self.charge_v[1]
            self.charge_frames -= 1
            hw, hh = self.width / 2, self.height / 2
            hit_wall = not (ARENA.left + hw <= self.x <= ARENA.right - hw and ARENA.top + hh <= self.y <= ARENA.bottom - hh)
            self.x = max(ARENA.left + hw, min(ARENA.right - hw, self.x))
            self.y = max(ARENA.top + hh, min(ARENA.bottom - hh, self.y))
            if self.charge_frames <= 0 or hit_wall:
                self.charging = False
                self.shake_request = 12
                self.ring(10 + 4 * self.phase, random.uniform(0, math.tau), self.bullet_vel)
                self.target = (self.x, self.y)
            return
        super().move(now)

    # Rozbeh priamo na hráča (najprv ukáže, kam poletí) #
    def attack_charge(self, now):
        self.telegraph = True
        self.charge_target = (self.player.x, self.player.y)
        self.charge_start = now + 650

    # Vodorovný laser #
    def attack_laser(self, now):
        self.laser(now, y=self.player.y)
        if self.phase >= 2:
            self.later(now + 500, lambda: self.laser(now + 500, y=self.player.y))

    # Rakety, ktoré naháňajú hráča #
    def attack_missiles(self, now):
        count = 2 + self.phase
        for i in range(count):
            a = -math.pi / 2 + (i - (count - 1) / 2) * 0.6
            self.later(now + i * 150, lambda a=a: self.fire(
                self.x, self.y, math.cos(a) * self.bullet_vel, math.sin(a) * self.bullet_vel,
                radius=11, homing=0.05, homing_frames=110))
        self.sounds.play("boss_shot")

    def attacks(self):
        attacks = [self.attack_charge, self.attack_laser, self.attack_missiles, self.attack_cross]
        if self.phase >= 2:
            attacks += [self.attack_laser_cross, self.attack_walls]
        return attacks

    def draw(self, surf, now):
        if self.telegraph and (now // 80) % 2:
            steps = 14
            for i in range(0, steps, 2):
                t1, t2 = i / steps, (i + 1) / steps
                p1 = (self.x + (self.charge_target[0] - self.x) * t1, self.y + (self.charge_target[1] - self.y) * t1)
                p2 = (self.x + (self.charge_target[0] - self.x) * t2, self.y + (self.charge_target[1] - self.y) * t2)
                pygame.draw.line(surf, RED, p1, p2, 4)
        if self.telegraph:
            real_x = self.x
            self.x += random.uniform(-3, 3)
            super().draw(surf, now)
            self.x = real_x
        else:
            super().draw(surf, now)

# # # 5. KAZETA: KRÁĽ PÁSOK # # #

class TapeKing(Boss):
    name = "KRÁĽ PÁSOK"
    sprites = [[
        ".....y..y..y..y.....",
        ".....yyyyyyyyyy.....",
        ".....yryyyyyyry.....",
        "kkkkkkkkkkkkkkkkkkkk",
        "kbbbbbbbbbbbbbbbbbbk",
        "kbwwwwwwwwwwwwwwwwbk",
        "kbbkkkkkkkkkkkkkkbbk",
        "kbbkgRRRggggRRRgkbbk",
        "kbbkRReRRggRReRRkbbk",
        "kbbkgRRRggggRRRgkbbk",
        "kbbkkkkkkkkkkkkkkbbk",
        "kbbbbkkkkkkkkkkbbbbk",
        "kbbbbktktktktkkbbbbk",
        "kkkkkkkkkkkkkkkkkkkk",
    ]]
    base = {"k": (20, 10, 20), "b": (45, 40, 55), "g": (15, 15, 25), "R": (230, 230, 240),
            "e": (40, 20, 40), "y": GOLD, "r": RED, "t": WHITE}
    palettes = [{**base, "w": PINK}, {**base, "w": CYAN}, {**base, "w": YELLOW}]
    anim = [{}, {"R": (150, 150, 170)}]
    colors = (PINK, CYAN, YELLOW)
    phase_marks = (0.66, 0.33)
    hp_mult = 3.2

    # Pretáčanie – strely odletia a potom sa vrátia späť #
    def attack_rewind(self, now):
        self.ring(14 + 4 * self.phase, random.uniform(0, math.tau), self.bullet_vel * 1.1,
                 reverse_after=55)
        self.osd = ("REW", now + 1600)

    # Šum – strely zo všetkých okrajov #
    def attack_static(self, now):
        v = self.bullet_vel
        for _ in range(14 + 4 * self.phase):
            side = random.randrange(4)
            if side == 0:
                x, y = ARENA.left + 8, random.uniform(ARENA.top + 20, ARENA.bottom - 20)
            elif side == 1:
                x, y = ARENA.right - 8, random.uniform(ARENA.top + 20, ARENA.bottom - 20)
            elif side == 2:
                x, y = random.uniform(ARENA.left + 20, ARENA.right - 20), ARENA.top + 8
            else:
                x, y = random.uniform(ARENA.left + 20, ARENA.right - 20), ARENA.bottom - 8
            a = math.atan2(ARENA.centery + random.uniform(-150, 150) - y, ARENA.centerx + random.uniform(-200, 200) - x)
            self.fire(x, y, math.cos(a) * v, math.sin(a) * v, WARNING_TIME + random.randint(0, 400), radius=7)
        self.sounds.play("boss_shot")

    def attacks(self):
        attacks = [self.attack_rewind, self.attack_cross, self.attack_aimed, self.attack_walls]
        if self.phase >= 2:
            attacks += [self.attack_laser_cross, self.attack_homing, self.attack_spiral]
        if self.phase >= 3:
            attacks += [self.attack_rain, self.attack_static, self.attack_rewind]
        return attacks

# # # ZOZNAM KAZIET (LEVELOV) # # #

LEVELS = [
    {"title": "Neónové mesto", "boss": Guardian, "theme": THEMES[0]},
    {"title": "Invázia z vesmíru", "boss": Ufo, "theme": THEMES[1]},
    {"title": "Strašidelný dom", "boss": Ghost, "theme": THEMES[2]},
    {"title": "Oceľová továreň", "boss": Robot, "theme": THEMES[3]},
    {"title": "Kráľ pások", "boss": TapeKing, "theme": THEMES[4]},
]
