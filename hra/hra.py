# # # PREKLIATE KAZETY – HRA NA ROČNÍKOVÚ PRÁCU # # #
# Spustenie: python hra.py #

# # # IMPORTOVANIA # # #

import json
import math
import os
import random
import sys

import pygame

# Ostatné súbory hry musia byť v tom istom priečinku ako hra.py #
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
if not os.path.exists(os.path.join(HERE, "nastavenia.py")):
    print("\nCHYBA: V priečinku s hra.py chýbajú ostatné súbory hry (nastavenia.py, grafika.py, ...).")
    print("Hru si pravdepodobne spustil priamo zo ZIP súboru.")
    print("Klikni na ZIP pravým tlačidlom -> 'Extrahovať všetko...' a spusti hra.py z rozbaleného priečinka.")
    print("Aktuálny priečinok:", HERE)
    input("\nStlač Enter na ukončenie...")
    sys.exit(1)

from nastavenia import *
from grafika import (FONT, FONT_BIG, FONT_HUGE, FONT_SMALL, HEART_EMPTY, HEART_FULL, Background, VhsFilter,
                     blit_glow, dim, draw_pause_icon, draw_play_icon, draw_rewind_icon, draw_text, make_sprite,
                     silhouette, timecode)
from efekty import FloatingText, Shockwave, burst
from strely import circle_hits_rect
from hrac import Player
from bossovia import LEVELS
from zvuky import Sounds
import vylepsenia

# # # UKLADANIE # # #

def load_save():
    data = {"highscores": {}, "best_level": 1, "vhs": True, "sound": True, "difficulty": 1}
    try:
        with open(SAVE_FILE, encoding="utf-8") as f:
            data.update(json.load(f))
    except (OSError, ValueError):
        pass
    return data


def write_save(data):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def wrap_text(text, font, width):
    lines, line = [], ""
    for word in text.split():
        test = (line + " " + word).strip()
        if font.size(test)[0] <= width:
            line = test
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines

# # # HRA # # #

class Game:
    def __init__(self):
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Prekliate kazety – hra na ročníkovú prácu")
        self.canvas = pygame.Surface((WIDTH, HEIGHT)).convert()
        self.clock = pygame.time.Clock()
        self.save = load_save()
        self.sounds = Sounds(self.save["sound"])
        self.sounds.start_music()
        self.vhs = VhsFilter()
        self.background = Background(THEMES[0])
        self.difficulty = self.save["difficulty"] % len(DIFFICULTIES)
        self.running = True
        self.menu_index = 0
        self.pause_index = 0
        self.menu_rects = []
        self.shake = 0

        # Malé obrázky bossov do menu (neodomknutí sú len tmavé siluety) #
        self.shelf = []
        for level in LEVELS:
            boss = level["boss"]
            self.shelf.append((make_sprite(boss.sprites[0], boss.palettes[0], 3),
                               silhouette(boss.sprites[0], (45, 40, 70), 3)))

        self.start_run()
        self.go_menu()

    # # # PRÍPRAVA HRY # # #

    def start_run(self):
        diff = DIFFICULTIES[self.difficulty]
        self.player = Player(diff["player_health"])
        self.level = 0
        self.stats = {"kill": 0, "hit": 0, "miss": 0, "hurt": 0, "bomb": 0}
        self.bosses_beaten = 0
        self.run_time = 0
        self.start_level()

    def start_level(self):
        level = LEVELS[self.level]
        self.background.set_theme(level["theme"])
        self.game_time = 0
        self.player_bullets = []
        self.boss_bullets = []
        self.particles = []
        self.texts = []
        self.shockwaves = []
        self.player.start_level()
        self.boss = level["boss"](DIFFICULTIES[self.difficulty], self.boss_bullets, self.sounds, self.player)
        self.ending = False
        self.won = False
        self.end_time = 0
        self.hurt_flash = 0
        self.banner = None
        self.final_score = 0
        self.new_record = False
        self.set_state("intro")
        if self.level + 1 > self.save["best_level"]:
            self.save["best_level"] = self.level + 1
            write_save(self.save)

    def set_state(self, state):
        self.state = state
        self.state_start = pygame.time.get_ticks()
        self.pause_index = 0
        self.menu_rects = []

    def go_menu(self):
        self.background.set_theme(THEMES[0])
        self.menu_index = 0
        self.set_state("menu")

    # # # HLAVNÁ SLUČKA # # #

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
                self.toggle_sound()
        getattr(self, "state_" + self.state)(dt, events)

        frame = self.vhs.apply(self.canvas) if self.save["vhs"] else self.canvas

        # Trasenie obrazovky #
        offset = (0, 0)
        if self.shake > 0.5:
            offset = (random.uniform(-self.shake, self.shake), random.uniform(-self.shake, self.shake))
            self.shake *= 0.88
        else:
            self.shake = 0
        self.win.fill(BLACK)
        self.win.blit(frame, offset)
        pygame.display.flip()

    def toggle_sound(self):
        self.sounds.toggle()
        self.save["sound"] = self.sounds.enabled
        write_save(self.save)

    # # # MENU (klávesnica aj myš) # # #

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

    def draw_menu_items(self, items, index, top, spacing=52):
        self.menu_rects = []
        now = pygame.time.get_ticks()
        for i, label in enumerate(items):
            rect = pygame.Rect(0, 0, 440, 44)
            rect.center = (WIDTH // 2, top + i * spacing)
            if i == index:
                grow = int(math.sin(now / 150) * 3)
                box = rect.inflate(grow * 2, 0)
                highlight = pygame.Surface(box.size, pygame.SRCALPHA)
                highlight.fill((*GOLD, 45))
                self.canvas.blit(highlight, box)
                pygame.draw.rect(self.canvas, GOLD, box, 3)
                draw_play_icon(self.canvas, box.left + 14, box.centery, 18, GOLD)
                draw_text(self.canvas, label, FONT, GOLD, rect.center)
            else:
                draw_text(self.canvas, label, FONT, GREY, rect.center)
            self.menu_rects.append(rect)

    def draw_title(self, text, y, color=GOLD, font=FONT_HUGE):
        blit_glow(self.canvas, 170, dim(color, 0.35), (WIDTH // 2, int(y)), 0.8)
        draw_text(self.canvas, text, font, color, (WIDTH // 2, int(y)))

    def draw_overlay(self, alpha=170):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 5, 15, alpha))
        self.canvas.blit(overlay, (0, 0))

    def draw_osd(self, label, icon="play"):
        # Nápis v rohu ako na starom videorekordéri #
        now = pygame.time.get_ticks()
        if icon == "play":
            draw_play_icon(self.canvas, 30, 32, 22, WHITE)
        elif icon == "pause":
            draw_pause_icon(self.canvas, 28, 32, 22, WHITE)
        draw_text(self.canvas, label, FONT, WHITE, (62, 32), "midleft")
        draw_text(self.canvas, "SP " + timecode(now), FONT, WHITE, (WIDTH - 28, 32), "midright")

    # # # STAV: HLAVNÉ MENU # # #

    def state_menu(self, dt, events):
        items = ["Hrať",
                 "Obtiažnosť: " + DIFFICULTIES[self.difficulty]["name"],
                 "Ovládanie",
                 "VHS efekt: " + ("zap." if self.save["vhs"] else "vyp."),
                 "Zvuk: " + ("zap." if self.sounds.enabled else "vyp."),
                 "Koniec"]
        self.menu_index, activated, delta = self.menu_input(events, len(items), self.menu_index)
        if self.menu_index == 1 and delta:
            self.change_difficulty(delta)
        if activated == 0:
            self.start_run()
        elif activated == 1:
            self.change_difficulty(1)
        elif activated == 2:
            self.set_state("controls")
        elif activated == 3:
            self.save["vhs"] = not self.save["vhs"]
            write_save(self.save)
        elif activated == 4:
            self.toggle_sound()
        elif activated == 5:
            self.running = False
        if self.state != "menu":
            return

        now = pygame.time.get_ticks()
        self.background.update()
        self.background.draw(self.canvas)
        if (now // 600) % 2:
            self.draw_osd("PLAY")
        else:
            draw_text(self.canvas, "SP " + timecode(now), FONT, WHITE, (WIDTH - 28, 32), "midright")
        self.draw_title("PREKLIATE KAZETY", 105 + math.sin(now / 700) * 4)
        draw_text(self.canvas, "Hra na ročníkovú prácu", FONT_SMALL, GREY, (WIDTH // 2, 158))

        # Polička s kazetami – odomknutí bossovia sú farební #
        for i, (sprite, locked) in enumerate(self.shelf):
            x = WIDTH // 2 + (i - 2) * 150
            unlocked = i < self.save["best_level"]
            image = sprite if unlocked else locked
            bob = math.sin(now / 400 + i) * 3 if unlocked else 0
            self.canvas.blit(image, image.get_rect(center=(x, 222 + bob)))
            draw_text(self.canvas, f"KAZETA {i + 1}" if unlocked else "???", FONT_SMALL, GREY, (x, 272))

        self.draw_menu_items(items, self.menu_index, 330)
        name = DIFFICULTIES[self.difficulty]["name"]
        best = self.save["highscores"].get(name, 0)
        draw_text(self.canvas, f"Najlepšie skóre ({name}): {best}", FONT_SMALL, GOLD, (WIDTH // 2, 636))
        draw_text(self.canvas, "W/S - výber   A/D - zmena   Enter - potvrdiť", FONT_SMALL, GREY, (WIDTH // 2, 668))

    def change_difficulty(self, delta):
        self.difficulty = (self.difficulty + delta) % len(DIFFICULTIES)
        self.save["difficulty"] = self.difficulty
        write_save(self.save)
        self.sounds.play("move")

    # # # STAV: OVLÁDANIE # # #

    def state_controls(self, dt, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.sounds.play("select")
                self.go_menu()
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.go_menu()
                return

        self.background.update()
        self.background.draw(self.canvas)
        self.draw_title("OVLÁDANIE", 70, CYAN, FONT_BIG)
        panel = pygame.Rect(0, 0, 780, 520)
        panel.center = (WIDTH // 2, 385)
        box = pygame.Surface(panel.size, pygame.SRCALPHA)
        box.fill((20, 16, 45, 225))
        self.canvas.blit(box, panel)
        pygame.draw.rect(self.canvas, ARENA_BORDER, panel, 3)

        rows = [("W A S D", "pohyb"),
                ("Šípky", "streľba (aj šikmo)"),
                ("Medzerník", "úskok - si pri ňom nezraniteľný"),
                ("E / Shift", "bomba - zničí strely, zraní bossa"),
                ("ESC / P", "pauza"),
                ("M", "zvuk zapnúť / vypnúť")]
        for i, (key, action) in enumerate(rows):
            y = panel.top + 40 + i * 42
            draw_text(self.canvas, key, FONT, GOLD, (panel.left + 230, y), "midright")
            draw_text(self.canvas, action, FONT_SMALL, WHITE, (panel.left + 255, y), "midleft")

        tips = ["Hra má 5 kaziet a na každej čaká iný boss.",
                "Po výhre si vyberieš 1 z 3 vylepšení.",
                "Bomba sa nabíja zásahmi (pásik dole).",
                "Blikajúce bodky = o chvíľu tam niečo vystrelí.",
                "Trafená strela +50, netrafená -10, zranenie -100."]
        for i, tip in enumerate(tips):
            draw_text(self.canvas, tip, FONT_SMALL, GREY, (WIDTH // 2, panel.top + 315 + i * 34))
        draw_text(self.canvas, "ESC / Enter - späť", FONT_SMALL, GOLD, (WIDTH // 2, 670))

    # # # STAV: ÚVOD KAZETY # # #

    def state_intro(self, dt, events):
        elapsed = pygame.time.get_ticks() - self.state_start
        for event in events:
            if event.type == pygame.KEYDOWN and elapsed > 600:
                if event.key == pygame.K_ESCAPE:
                    self.go_menu()
                    return
                elapsed = 10 ** 6
        if elapsed > 3200:
            self.set_state("play")
            self.banner = ("PLAY", 1200)
            self.vhs.kick(6)
            return

        now = pygame.time.get_ticks()
        level = LEVELS[self.level]
        accent = level["theme"]["accent"]
        self.background.update()
        self.background.draw(self.canvas)
        self.draw_overlay(90)
        self.draw_osd("PLAY" if (now // 500) % 2 else "")

        # Kazeta sa zasúva zdola #
        slide = max(0, 1 - elapsed / 500) ** 2 * 400
        body = pygame.Rect(0, 0, 600, 330)
        body.center = (WIDTH // 2, HEIGHT // 2 + 10 + slide)
        pygame.draw.rect(self.canvas, (30, 28, 38), body)
        pygame.draw.rect(self.canvas, (70, 66, 86), body, 6)
        label = pygame.Rect(body.left + 40, body.top + 30, body.width - 80, 130)
        pygame.draw.rect(self.canvas, accent, label)
        pygame.draw.rect(self.canvas, dim(accent, 0.5), label, 4)
        for k in range(3):
            pygame.draw.line(self.canvas, dim(accent, 0.7), (label.left + 10, label.bottom - 14 - k * 8),
                             (label.right - 10, label.bottom - 14 - k * 8), 2)
        draw_text(self.canvas, f"KAZETA {self.level + 1}/{len(LEVELS)}", FONT_BIG, DARK,
                  (label.centerx, label.top + 38), shadow=False)
        draw_text(self.canvas, level["title"].upper(), FONT, DARK, (label.centerx, label.top + 82), shadow=False)

        window = pygame.Rect(0, 0, 360, 110)
        window.midtop = (body.centerx, label.bottom + 20)
        pygame.draw.rect(self.canvas, (12, 12, 18), window)
        pygame.draw.rect(self.canvas, (70, 66, 86), window, 4)
        for side in (-1, 1):
            cx, cy = window.centerx + side * 105, window.centery
            pygame.draw.circle(self.canvas, (60, 40, 30), (cx, cy), 42)
            pygame.draw.circle(self.canvas, (220, 220, 230), (cx, cy), 20)
            for spoke in range(6):
                a = now / 200 + spoke * math.tau / 6
                pygame.draw.line(self.canvas, (60, 60, 70), (cx, cy), (cx + math.cos(a) * 18, cy + math.sin(a) * 18), 3)

        draw_text(self.canvas, "BOSS: " + level["boss"].name, FONT, accent, (WIDTH // 2, body.bottom + 40))
        if elapsed > 600 and (now // 400) % 2:
            draw_text(self.canvas, "Stlač ľubovoľný kláves", FONT_SMALL, GREY, (WIDTH // 2, body.bottom + 78))

    # # # STAV: SAMOTNÁ HRA # # #

    def state_play(self, dt, events):
        keys = pygame.key.get_pressed()
        for event in events:
            if event.type == pygame.KEYDOWN and not self.ending:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    self.set_state("pause")
                    self.sounds.play("select")
                elif event.key == pygame.K_SPACE:
                    if self.player.try_dash(keys, self.game_time):
                        self.sounds.play("dash")
                elif event.key in (pygame.K_e, pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self.use_bomb()
        if self.state != "play":
            self.draw_scene()
            return

        self.game_time += dt
        self.run_time += dt
        now = self.game_time
        player, boss = self.player, self.boss

        if not self.ending:
            player.update(keys, now)
            bullets = player.try_shoot(keys, now)
            if bullets:
                self.player_bullets.extend(bullets)
                self.sounds.play("shoot")
            if boss.update(now):
                self.on_phase_change()
            if boss.shake_request:
                self.shake = max(self.shake, boss.shake_request)
                boss.shake_request = 0

        # Strely hráča #
        for bullet in self.player_bullets[:]:
            bullet.update(dt, boss)
            if (boss.health > 0 and not boss.invulnerable
                    and circle_hits_rect(bullet.x, bullet.y, bullet.radius, boss.rect)):
                self.player_bullets.remove(bullet)
                self.on_boss_hit(bullet)
            elif bullet.outside(ARENA):
                self.player_bullets.remove(bullet)
                burst(self.particles, bullet.x, bullet.y, 4, [CYAN], 2, 15, 2)
                if not self.ending:
                    self.stats["miss"] += MISS_SCORE

        # Strely nepriateľa #
        for bullet in self.boss_bullets[:]:
            bullet.update(dt, player)
            if not bullet.active:
                continue
            if bullet.dead or bullet.outside(ARENA, 30):
                self.boss_bullets.remove(bullet)
            elif (not self.ending and not player.is_invincible(now)
                  and circle_hits_rect(bullet.x, bullet.y, bullet.radius, player.hitbox)):
                self.boss_bullets.remove(bullet)
                self.on_player_hit()

        # Dotyk s bossom tiež zraňuje #
        if (not self.ending and not player.is_invincible(now) and boss.alpha > 150
                and player.hitbox.colliderect(boss.rect.inflate(-10, -10))):
            self.on_player_hit()

        self.update_effects()
        self.background.update(1 + boss.phase)

        # Koniec kazety #
        if not self.ending:
            if boss.health <= 0:
                self.start_ending(True)
            elif player.health <= 0:
                self.start_ending(False)
        elif now >= self.end_time:
            if not self.won:
                self.finish_run(False)
            elif self.level < len(LEVELS) - 1:
                self.enter_upgrade()
            else:
                self.finish_run(True)
            return

        self.draw_scene()

    def update_effects(self):
        for particle in self.particles:
            particle.update()
        self.particles = [p for p in self.particles if p.life > 0]
        for text in self.texts:
            text.update()
        self.texts = [t for t in self.texts if t.life > 0]
        for wave in self.shockwaves:
            wave.update()
        self.shockwaves = [w for w in self.shockwaves if w.life > 0]
        self.hurt_flash = max(0, self.hurt_flash - 1)

    # # # UDALOSTI V HRE # # #

    def on_boss_hit(self, bullet):
        boss, player = self.boss, self.player
        boss.health -= bullet.damage
        boss.flash = 4
        self.stats["hit"] += HIT_SCORE
        charge = bullet.damage / BOMB_HITS * (1 + 0.4 * player.level("bomb"))
        player.bomb_charge = min(1.0, player.bomb_charge + charge)
        burst(self.particles, bullet.x, bullet.y, 8, [LIGHT_CYAN, boss.color, WHITE], 4, 25, 3)
        if bullet.crit:
            self.texts.append(FloatingText(bullet.x, bullet.y - 10, "KRIT!", GOLD))
        else:
            self.texts.append(FloatingText(bullet.x, bullet.y - 10, f"+{HIT_SCORE}", GOLD))
        self.sounds.play("hit")
        self.shake = max(self.shake, 2)

    def on_player_hit(self):
        player = self.player
        if player.take_hit(self.game_time):
            self.stats["hurt"] += HURT_SCORE
            burst(self.particles, player.x, player.y, 20, [CYAN, PINK, WHITE], 5, 35, 4)
            self.texts.append(FloatingText(player.x, player.y - 25, str(HURT_SCORE), RED))
            self.sounds.play("hurt")
            self.shake = 12
            self.hurt_flash = 14
            self.vhs.kick(6)
        else:
            burst(self.particles, player.x, player.y, 16, [BLUE, LIGHT_CYAN], 5, 30, 3)
            self.texts.append(FloatingText(player.x, player.y - 25, "ŠTÍT!", LIGHT_CYAN))
            self.sounds.play("shield")
            self.shake = 5

    def use_bomb(self):
        player, boss = self.player, self.boss
        if player.bomb_charge < 1:
            return
        player.bomb_charge = 0
        cleared = len(self.boss_bullets)
        for bullet in self.boss_bullets:
            burst(self.particles, bullet.x, bullet.y, 2, [bullet.color, WHITE], 2, 20, 2)
        self.boss_bullets.clear()
        self.stats["bomb"] += cleared * BOMB_BULLET_SCORE
        boss.health -= player.bomb_damage
        boss.flash = 10
        self.shockwaves.append(Shockwave(player.x, player.y, GOLD))
        self.shockwaves.append(Shockwave(player.x, player.y, WHITE, 500))
        self.texts.append(FloatingText(boss.x, boss.y - boss.height // 2 - 15, f"-{player.bomb_damage}", GOLD))
        self.sounds.play("bomb")
        self.shake = 16
        self.vhs.kick(10)

    def on_phase_change(self):
        boss = self.boss
        self.banner = (f"FÁZA {boss.phase}!", self.game_time + 1800)
        self.shake = 18
        self.vhs.kick(12)
        burst(self.particles, boss.x, boss.y, 60, [boss.color, GOLD, WHITE], 8, 50, 5)
        self.sounds.play("phase")

    def start_ending(self, won):
        self.ending = True
        self.won = won
        self.end_time = self.game_time + END_DELAY
        self.shake = 25
        self.vhs.kick(14)
        self.sounds.play("explode")
        if won:
            self.bosses_beaten += 1
            self.stats["kill"] += KILL_SCORE * (self.level + 1)
            self.boss.scheduled.clear()
            burst(self.particles, self.boss.x, self.boss.y, 150, [self.boss.color, ORANGE, GOLD, WHITE], 9, 80, 7)
            for bullet in self.boss_bullets:
                burst(self.particles, bullet.x, bullet.y, 3, [bullet.color], 2, 20, 3)
            self.boss_bullets.clear()
            self.banner = ("STOP", self.game_time + END_DELAY)
        else:
            burst(self.particles, self.player.x, self.player.y, 90, [CYAN, LIGHT_CYAN, WHITE], 7, 70, 5)

    def enter_upgrade(self):
        self.choices = vylepsenia.upgrade_choices(self.player.upgrades)
        self.healed = self.player.health < self.player.max_health
        self.player.health = min(self.player.max_health, self.player.health + 1)
        self.set_state("upgrade")
        self.upgrade_index = 1

    def finish_run(self, won):
        self.won = won
        score = sum(self.stats.values())
        self.final_score = max(0, round(score * DIFFICULTIES[self.difficulty]["mult"]))
        name = DIFFICULTIES[self.difficulty]["name"]
        self.new_record = self.final_score > self.save["highscores"].get(name, 0)
        if self.new_record:
            self.save["highscores"][name] = self.final_score
            write_save(self.save)
        self.set_state("game_over")

    # # # VYKRESLENIE HRY # # #

    def draw_scene(self):
        c = self.canvas
        now = self.game_time
        self.background.draw(c)
        arena = pygame.Surface(ARENA.size, pygame.SRCALPHA)
        arena.fill((0, 0, 0, 70))
        c.blit(arena, ARENA)
        pygame.draw.rect(c, ARENA_BORDER, ARENA, 3)

        if not (self.ending and self.won):
            self.boss.draw(c, now)
        if not (self.ending and not self.won):
            self.player.draw(c, now)
        for bullet in self.player_bullets:
            bullet.draw(c, now)
        for bullet in self.boss_bullets:
            bullet.draw(c, now)
        for particle in self.particles:
            particle.draw(c)
        for wave in self.shockwaves:
            wave.draw(c)
        for text in self.texts:
            text.draw(c)

        if self.hurt_flash:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 0, 40, self.hurt_flash * 6))
            c.blit(flash, (0, 0))

        # Veľké nápisy (PLAY, FÁZA 2!, STOP) #
        if self.banner and now < self.banner[1]:
            text = self.banner[0]
            if text == "PLAY":
                draw_play_icon(c, WIDTH // 2 - 140, HEIGHT // 2 - 40, 60, WHITE)
                draw_text(c, "PLAY", FONT_HUGE, WHITE, (WIDTH // 2 + 40, HEIGHT // 2 - 40))
            elif text == "STOP":
                c.fill(WHITE, (WIDTH // 2 - 150, HEIGHT // 2 - 68, 56, 56))
                draw_text(c, "STOP", FONT_HUGE, WHITE, (WIDTH // 2 + 40, HEIGHT // 2 - 40))
            else:
                draw_text(c, text, FONT_HUGE, self.boss.color, (WIDTH // 2, HEIGHT // 2 - 40))

        if self.boss.osd and now < self.boss.osd[1] and (now // 150) % 2:
            draw_rewind_icon(c, WIDTH // 2 - 90, 110, 30, WHITE)
            draw_text(c, self.boss.osd[0], FONT_BIG, WHITE, (WIDTH // 2 + 25, 110))

        self.draw_hud()

    def draw_hud(self):
        c = self.canvas
        player, boss = self.player, self.boss

        # Životy hráča a štít #
        for i in range(player.max_health):
            c.blit(HEART_FULL if i < player.health else HEART_EMPTY, (22 + i * 26, 14))
        if player.level("shield"):
            x = 34 + player.max_health * 26
            pygame.draw.circle(c, BLUE if player.shield else (50, 50, 80), (x, 23), 10, 3)

        # Životy bossa #
        bar = pygame.Rect(0, 0, 400, 16)
        bar.center = (WIDTH // 2, 46)
        draw_text(c, boss.name, FONT_SMALL, boss.color, (WIDTH // 2, 20))
        pygame.draw.rect(c, DARK, bar.inflate(6, 6))
        shown = max(0.0, boss.shown_health / boss.max_health)
        real = max(0.0, boss.health / boss.max_health)
        c.fill(WHITE, (bar.left, bar.top, bar.width * shown, bar.height))
        c.fill(boss.color, (bar.left, bar.top, bar.width * real, bar.height))
        for mark in boss.phase_marks:
            x = bar.left + bar.width * mark
            pygame.draw.line(c, GREY, (x, bar.top - 3), (x, bar.bottom + 3), 3)
        pygame.draw.rect(c, GREY, bar.inflate(6, 6), 2)

        # Skóre #
        draw_text(c, f"SKÓRE {sum(self.stats.values())}", FONT, GOLD, (WIDTH - 22, 30), "midright")

        # Spodná lišta: úskok, bomba, časomiera #
        ready = min(1.0, 1 - (player.next_dash - self.game_time) / player.dash_cooldown)
        self.draw_meter("ÚSKOK", 22, ready, CYAN)
        blink = player.bomb_charge >= 1 and (pygame.time.get_ticks() // 250) % 2
        self.draw_meter("BOMBA", 230, player.bomb_charge, WHITE if blink else ORANGE)
        draw_play_icon(c, WIDTH // 2 + 60, HEIGHT - 19, 16, WHITE)
        draw_text(c, f"KAZETA {self.level + 1}  {timecode(self.run_time)}", FONT_SMALL, WHITE,
                  (WIDTH // 2 + 84, HEIGHT - 19), "midleft")
        draw_text(c, "ESC pauza", FONT_SMALL, GREY, (WIDTH - 22, HEIGHT - 19), "midright")

    def draw_meter(self, label, x, value, color):
        c = self.canvas
        draw_text(c, label, FONT_SMALL, WHITE, (x, HEIGHT - 19), "midleft")
        meter = pygame.Rect(x + 72, HEIGHT - 27, 110, 14)
        c.fill(DARK, meter)
        c.fill(color if value >= 1 else dim(color, 0.55),
               (meter.left, meter.top, meter.width * max(0.0, value), meter.height))
        pygame.draw.rect(c, GREY, meter, 2)

    def draw_upgrade_row(self, y):
        # Malé ikonky vylepšení, ktoré hráč už má #
        owned = list(self.player.upgrades.items())
        if not owned:
            return
        x = WIDTH // 2 - len(owned) * 62 // 2
        for key, lvl in owned:
            self.canvas.blit(vylepsenia.icon(key, 4), (x + 3, y))
            draw_text(self.canvas, str(lvl), FONT_SMALL, WHITE, (x + 38, y + 24), "midleft")
            x += 62

    # # # STAV: PAUZA # # #

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
            self.start_run()
        elif activated == 2:
            self.go_menu()
        if self.state != "pause":
            return
        self.draw_scene()
        self.draw_overlay()
        draw_pause_icon(self.canvas, WIDTH // 2 - 160, 200, 56, CYAN)
        draw_text(self.canvas, "PAUZA", FONT_HUGE, CYAN, (WIDTH // 2 + 40, 200))
        self.draw_menu_items(items, self.pause_index, 330)
        if self.player.upgrades:
            draw_text(self.canvas, "Tvoje vylepšenia", FONT_SMALL, GREY, (WIDTH // 2, 520))
            self.draw_upgrade_row(545)

    # # # STAV: VÝBER VYLEPŠENIA # # #

    def state_upgrade(self, dt, events):
        count = len(self.choices)
        index, activated, delta = self.menu_input(events, count, self.upgrade_index)
        self.upgrade_index = (index + delta) % count
        if delta:
            self.sounds.play("move")
        for event in events:
            if event.type == pygame.KEYDOWN and pygame.K_1 <= event.key < pygame.K_1 + count:
                activated = event.key - pygame.K_1
        if activated is not None:
            self.player.add_upgrade(self.choices[activated])
            self.sounds.play("upgrade")
            self.vhs.kick(8)
            self.level += 1
            self.start_level()
            return

        now = pygame.time.get_ticks()
        self.background.update()
        self.background.draw(self.canvas)
        self.draw_overlay(120)
        self.draw_title(f"KAZETA {self.level + 1} PREHRANÁ!", 70, GREEN, FONT_BIG)
        info = "Vyber si vylepšenie" + ("  (+1 život za výhru)" if self.healed else "")
        draw_text(self.canvas, info, FONT, WHITE, (WIDTH // 2, 125))

        self.menu_rects = []
        for i, key in enumerate(self.choices):
            card = pygame.Rect(0, 0, 270, 330)
            card.center = (WIDTH // 2 + (i - (count - 1) / 2) * 300, 350)
            selected = i == self.upgrade_index
            if selected:
                card.y -= 10 + int(math.sin(now / 150) * 3)
            color = vylepsenia.color(key)
            box = pygame.Surface(card.size, pygame.SRCALPHA)
            box.fill((20, 16, 45, 235))
            self.canvas.blit(box, card)
            if selected:
                blit_glow(self.canvas, 150, dim(color, 0.3), card.center, 0.8)
            pygame.draw.rect(self.canvas, GOLD if selected else dim(color, 0.6), card, 4 if selected else 2)

            icon = vylepsenia.icon(key)
            self.canvas.blit(icon, icon.get_rect(center=(card.centerx, card.top + 60)))
            draw_text(self.canvas, vylepsenia.name(key), FONT_SMALL, color, (card.centerx, card.top + 120))
            for j, line in enumerate(wrap_text(vylepsenia.description(key), FONT_SMALL, card.width - 30)):
                draw_text(self.canvas, line, FONT_SMALL, WHITE, (card.centerx, card.top + 165 + j * 26), shadow=False)
            current, maximum = self.player.level(key), vylepsenia.max_level(key)
            if maximum is not None:
                draw_text(self.canvas, f"Úroveň {current} > {current + 1} / {maximum}", FONT_SMALL, GREY,
                          (card.centerx, card.bottom - 50))
            draw_text(self.canvas, f"[{i + 1}]", FONT_SMALL, GOLD if selected else GREY,
                      (card.centerx, card.bottom - 22))
            self.menu_rects.append(card)

        draw_text(self.canvas, f"Ďalej: KAZETA {self.level + 2} - {LEVELS[self.level + 1]['title']}", FONT_SMALL,
                  GREY, (WIDTH // 2, 550))
        self.draw_upgrade_row(575)
        draw_text(self.canvas, "A/D alebo myš - výber   Enter - potvrdiť", FONT_SMALL, GREY, (WIDTH // 2, 672))

    # # # STAV: KONIEC HRY # # #

    def state_game_over(self, dt, events):
        items = ["Hrať znova", "Hlavné menu"]
        self.pause_index, activated, _ = self.menu_input(events, len(items), self.pause_index)
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                activated = 1
        if activated == 0:
            self.start_run()
            return
        if activated == 1:
            self.go_menu()
            return

        self.update_effects()
        self.background.update()
        self.draw_scene()
        self.draw_overlay(200)

        if self.won:
            self.draw_title("VŠETKY KAZETY PREHRANÉ!", 70, GREEN, FONT_BIG)
        else:
            self.draw_title("PREHRAL SI!", 70, RED, FONT_HUGE)

        # Riadky sa objavujú postupne #
        elapsed = pygame.time.get_ticks() - self.state_start
        mult = DIFFICULTIES[self.difficulty]["mult"]
        name = DIFFICULTIES[self.difficulty]["name"]
        rows = [("Porazení bossovia", f"{self.bosses_beaten}/{len(LEVELS)}", WHITE),
                ("Body za bossov", str(self.stats["kill"]), WHITE),
                ("Strely trafené", str(self.stats["hit"]), WHITE),
                ("Strely netrafené", str(self.stats["miss"]), WHITE),
                ("Počet zranení", str(self.stats["hurt"]), WHITE),
                ("Zničené bombou", str(self.stats["bomb"]), WHITE),
                ("Násobič obtiažnosti", f"x{mult}", WHITE),
                ("Finálne skóre", str(self.final_score), GOLD),
                (f"Najlepšie ({name})", str(self.save["highscores"].get(name, 0)), GREY)]
        for i, (label, value, color) in enumerate(rows):
            if elapsed < 200 * (i + 1):
                break
            y = 140 + i * 38 + (12 if i >= 7 else 0)
            font = FONT_BIG if i == 7 else FONT
            draw_text(self.canvas, label, font, color, (WIDTH // 2 - 300, y), "midleft")
            draw_text(self.canvas, value, font, color, (WIDTH // 2 + 300, y), "midright")
            if i == 6:
                pygame.draw.line(self.canvas, GREY, (WIDTH // 2 - 300, y + 21), (WIDTH // 2 + 300, y + 21), 2)

        done = elapsed > 200 * len(rows)
        if done and self.new_record and (pygame.time.get_ticks() // 300) % 2:
            draw_text(self.canvas, "NOVÝ REKORD!", FONT_BIG, GOLD, (WIDTH // 2, 505))
        if done:
            self.draw_upgrade_row(530)
            self.draw_menu_items(items, self.pause_index, 610, 48)

# # # SPUSTENIE HRY # # #

if __name__ == "__main__":
    Game().run()
