# # # ZVUKY # # #
# Všetky zvuky aj hudba sa generujú priamo v kóde, takže hra nepotrebuje žiadne súbory #

import array
import math
import random

import pygame


def midi_to_freq(note):
    return 440 * 2 ** ((note - 69) / 12)


class Sounds:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.sounds = {}
        self.music = None
        self.music_channel = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.rate, _, self.channels = pygame.mixer.get_init()
            self.sounds = {
                "shoot": self.synth(900, 500, 0.06, 0.08),
                "hit": self.synth(320, 120, 0.08, 0.16),
                "hurt": self.synth(0, 0, 0.30, 0.35, noise=True),
                "shield": self.synth(1200, 300, 0.25, 0.20, wave="sine"),
                "boss_shot": self.synth(240, 160, 0.10, 0.08, wave="sine"),
                "laser": self.synth(1500, 200, 0.35, 0.14),
                "teleport": self.synth(200, 1400, 0.30, 0.15, wave="sine"),
                "explode": self.synth(0, 0, 1.00, 0.45, noise=True),
                "bomb": self.synth(80, 30, 0.80, 0.50),
                "select": self.synth(520, 880, 0.10, 0.18),
                "move": self.synth(420, 420, 0.04, 0.10),
                "upgrade": self.synth(400, 1600, 0.35, 0.20),
                "phase": self.synth(90, 420, 0.70, 0.30),
                "dash": self.synth(0, 0, 0.12, 0.15, noise=True),
            }
            self.music = self.make_music()
        except (pygame.error, TypeError, AttributeError):
            self.sounds = {}
            self.music = None

    def to_sound(self, samples):
        buf = array.array("h")
        for sample in samples:
            value = int(max(-1.0, min(1.0, sample)) * 32767)
            for _ in range(self.channels):
                buf.append(value)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def synth(self, f_start, f_end, duration, volume, wave="square", noise=False):
        samples = []
        count = int(self.rate * duration)
        phase = 0.0
        for i in range(count):
            t = i / count
            phase += (f_start + (f_end - f_start) * t) / self.rate
            if noise:
                value = random.uniform(-1, 1)
            elif wave == "square":
                value = 1.0 if phase % 1 < 0.5 else -1.0
            else:
                value = math.sin(phase * math.tau)
            samples.append(value * (1 - t) ** 2 * volume)
        return self.to_sound(samples)

    def make_music(self):
        # Jednoduchá synthwave slučka: basa, arpeggio, kopák a hi-hat (4 takty, 120 BPM) #
        rate = self.rate
        step_len = rate // 4  # osminová nota
        bass_notes = [45, 45, 41, 43]  # A, A, F, G
        chords = [[57, 60, 64], [57, 60, 64], [53, 57, 60], [55, 59, 62]]
        samples = []
        for bar in range(4):
            for step in range(8):
                bass_f = midi_to_freq(bass_notes[bar])
                arp_f = midi_to_freq(chords[bar][step % 3] + (12 if step >= 4 else 0))
                for i in range(step_len):
                    t = i / rate
                    env = 1 - i / step_len
                    value = (1 if (bass_f * t) % 1 < 0.5 else -1) * 0.12 * (0.4 + 0.6 * env)
                    value += math.sin(math.tau * arp_f * t) * 0.08 * env ** 2
                    if step % 4 == 0 and i < step_len // 2:
                        k = i / (step_len // 2)
                        value += math.sin(math.tau * (110 - 60 * k) * t) * 0.35 * (1 - k)
                    if step % 2 == 1 and i < step_len // 4:
                        value += random.uniform(-1, 1) * 0.04 * (1 - i / (step_len // 4))
                    samples.append(value)
        return self.to_sound(samples)

    def start_music(self):
        if self.music:
            self.music.set_volume(0.5)
            self.music_channel = self.music.play(loops=-1)
            if not self.enabled and self.music_channel:
                self.music_channel.pause()

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def toggle(self):
        self.enabled = not self.enabled
        if self.music_channel:
            if self.enabled:
                self.music_channel.unpause()
            else:
                self.music_channel.pause()
