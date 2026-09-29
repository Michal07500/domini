# # # VYLEPŠENIA # # #
# Po každej porazenej kazete si hráč vyberie 1 z 3 náhodných vylepšení #

import random

from grafika import make_sprite
from nastavenia import *

# kľúč: (názov, popis, maximálna úroveň alebo None = neobmedzene, farba, pixelová ikonka) #

UPGRADES = {
    "rate": ("Turbo spúšť", "Strieľaš o 20 % rýchlejšie.", 4, YELLOW, [
        "...xx..",
        "..xx...",
        ".xxxxx.",
        "...xx..",
        "..xx...",
        ".xx....",
        "x......"]),
    "multi": ("Rozptyl", "+1 strela navyše pri každom výstrele.", 3, CYAN, [
        "x..x..x",
        "x..x..x",
        ".......",
        "...o...",
        "..ooo..",
        "..ooo..",
        "......."]),
    "damage": ("Silné náboje", "Každá strela dá +1 poškodenie.", 3, RED, [
        "x..x..x",
        ".x.x.x.",
        "..xxx..",
        "xxxxxxx",
        "..xxx..",
        ".x.x.x.",
        "x..x..x"]),
    "size": ("Veľké náboje", "Väčšie a rýchlejšie strely.", 2, LIGHT_CYAN, [
        "..xxx..",
        ".xxxxx.",
        "xxooxxx",
        "xxoxxxx",
        "xxxxxxx",
        ".xxxxx.",
        "..xxx.."]),
    "homing": ("Navádzanie", "Strely sa stáčajú k bossovi.", 2, LIME, [
        "..xxx..",
        ".x...x.",
        "x..o..x",
        "x.ooo.x",
        "x..o..x",
        ".x...x.",
        "..xxx.."]),
    "back": ("Zadný kanón", "Strieľaš aj opačným smerom.", 1, BLUE, [
        "...x...",
        "..xxx..",
        ".x.x.x.",
        "...x...",
        ".x.x.x.",
        "..xxx..",
        "...x..."]),
    "crit": ("Kritický zásah", "20 % šanca na dvojnásobné poškodenie.", 2, GOLD, [
        "..xxx..",
        "..xxx..",
        "..xxx..",
        "..xxx..",
        "...x...",
        ".......",
        "..xxx.."]),
    "heart": ("Extra srdce", "+1 život navyše (aj ho hneď dostaneš).", 3, PINK, [
        ".xx.xx.",
        "xoxxxxx",
        "xxxxxxx",
        ".xxxxx.",
        "..xxx..",
        "...x...",
        "......."]),
    "speed": ("Rýchle tenisky", "Rýchlejší pohyb.", 2, TEAL, [
        "x..x...",
        ".x..x..",
        "..x..x.",
        "...x..x",
        "..x..x.",
        ".x..x..",
        "x..x..."]),
    "dash": ("Blesková nôžka", "Úskok sa nabíja o 35 % rýchlejšie.", 2, LILAC, [
        ".......",
        "xx..ooo",
        "...oooo",
        "xxx.ooo",
        "...oooo",
        "xx..ooo",
        "......."]),
    "shield": ("Štít", "Zachytí 1 zásah a po čase sa obnoví.", 2, BLUE, [
        "xxxxxxx",
        "xooooox",
        "xooooox",
        "xooooox",
        ".xooox.",
        "..xox..",
        "...x..."]),
    "bomb": ("Silnejšia bomba", "Bomba sa nabíja rýchlejšie a viac bolí.", 3, ORANGE, [
        "....x..",
        "...x...",
        "..xxx..",
        ".xxxxx.",
        ".xxoxx.",
        ".xxxxx.",
        "..xxx.."]),
    "heal": ("Oprava pásky", "Doplní všetky životy.", None, GREEN, [
        "..xxx..",
        "..xxx..",
        "xxxxxxx",
        "xxxxxxx",
        "xxxxxxx",
        "..xxx..",
        "..xxx.."]),
}


def name(key):
    return UPGRADES[key][0]


def description(key):
    return UPGRADES[key][1]


def max_level(key):
    return UPGRADES[key][2]


def color(key):
    return UPGRADES[key][3]


_icon_cache = {}


def icon(key, scale=6):
    if (key, scale) not in _icon_cache:
        c = color(key)
        _icon_cache[(key, scale)] = make_sprite(UPGRADES[key][4], {"x": c, "o": WHITE}, scale)
    return _icon_cache[(key, scale)]


def upgrade_choices(levels, count=3):
    available = [key for key in UPGRADES
                 if max_level(key) is None or levels.get(key, 0) < max_level(key)]
    return random.sample(available, min(count, len(available)))
