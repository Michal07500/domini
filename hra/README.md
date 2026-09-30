# Prekliate kazety – hra na ročníkovú prácu

Pixelová boss-rush hra v Pygame s atmosférou starých VHS kaziet. Celá grafika, zvuky aj hudba
sa kreslia/generujú priamo v kóde, netreba žiadne ďalšie súbory.

## Spustenie
```
pip install pygame
python hra.py
```

## Ovládanie
| Kláves | Akcia |
|---|---|
| W A S D | pohyb |
| Šípky | streľba (dá sa aj šikmo) |
| Medzerník | úskok – počas neho si nezraniteľný |
| E / Shift | bomba – zničí všetky strely a zraní bossa (nabíja sa zásahmi) |
| ESC / P | pauza |
| M | zvuk zapnúť / vypnúť |

## Kazety (levely)
| # | Prostredie | Boss | Špecialita |
|---|---|---|---|
| 1 | Neónové mesto | **Strážca** | pôvodné útoky (kríž, dvojitá vlna, steny) + kruh, mierené dávky, špirála |
| 2 | Invázia z vesmíru | **Vetrelec** (UFO) | dážď striel, ťažný lúč (laser), vejár |
| 3 | Strašidelný dom | **Strašidlo** | mizne a objavuje sa inde, navádzané gule, stena s medzerou |
| 4 | Oceľová továreň | **MECHA-9** | rozbeh na hráča, lasery, navádzané rakety |
| 5 | Kráľ pások | **Kráľ pások** | 3 fázy, „pretáčanie“ – strely sa vracajú späť, šum z okrajov |

Každý boss má viac fáz (vyznačené na pásiku životov) – v ďalšej fáze zmení farbu, zrýchli a pridá útoky.

## Vylepšenia
Po každej porazenej kazete dostaneš +1 život a vyberieš si 1 z 3 náhodných vylepšení:
Turbo spúšť, Rozptyl, Silné náboje, Veľké náboje, Navádzanie, Zadný kanón, Kritický zásah,
Extra srdce, Rýchle tenisky, Blesková nôžka, Štít, Silnejšia bomba, Oprava pásky.

## VHS vzhľad
Obraz sa zmenší a znova zväčší (hrubé pixely), posunie sa červená farba, pridajú sa riadky,
tmavé rohy a občas sa obraz „trhne“ ako pokazená páska. V menu sa dá vypnúť (VHS efekt: vyp.),
ak by hra na slabšom počítači sekala.

## Súbory
| Súbor | Čo obsahuje |
|---|---|
| `hra.py` | hlavná slučka, menu, stavy hry, HUD |
| `nastavenia.py` | všetky konštanty, farby, obtiažnosti, prostredia |
| `grafika.py` | fonty, pixelové sprity, pozadie, VHS efekt |
| `hrac.py` | hráč a jeho vylepšenia |
| `bossovia.py` | všetci bossovia, ich útoky a zoznam kaziet |
| `strely.py` | strely (aj navádzané, lasery, vracajúce sa) |
| `vylepsenia.py` | zoznam vylepšení |
| `efekty.py` | častice, vyskakujúci text, tlaková vlna |
| `zvuky.py` | generované zvuky a hudba |

Postup, najlepšie skóre a nastavenia sa ukladajú do `ulozenie.json`.

## Opravené chyby z pôvodného kódu
- Argumenty do `main()` sa posielali v zlom poradí (prehodené `next_boss_move` a prahové časy).
- `kill_score` sa pripočítaval každý snímok, kým mal boss 0 životov.
- Pohyb šikmo používal `PLAYER_VEL - 6` (= −1), takže bol pomalší/nerovnomerný.
- Mazanie striel zo zoznamu počas prechádzania cez ten istý zoznam (niektoré strely sa preskočili).
- `pygame.time.delay()` zamrazil okno na začiatku aj na konci hry.
- `FONT.render(..., WIDTH)` – farba textu bola číslo 1000 namiesto farby.
