# Posledný strážca – hra na ročníkovú prácu

Boss fight v Pygame. Celá grafika aj zvuky sa kreslia/generujú priamo v kóde, netreba žiadne ďalšie súbory.

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
| ESC / P | pauza |
| M | zvuk zapnúť / vypnúť |

## Čo je nové oproti pôvodnej verzii
- **Hlavné menu** (ovládanie klávesnicou aj myšou), výber obtiažnosti, obrazovka s ovládaním, pauza.
- **Grafika:** neónový štýl, žiariace strely so stopou, častice, trasenie obrazovky, boss s očami, ktoré sledujú hráča.
- **Boss má 2 fázy** – v polovici životov zrýchli a pridá útok špirálou. Spolu 6 typov útokov
  (pôvodné 3 zostali, pribudol kruh, mierené dávky a špirála).
- Strely z okrajov najprv **blikajú ako varovanie**.
- **Úskok** so zobrazeným cooldownom, hráč má menší hitbox (férovejšie uhýbanie).
- Životy ako srdiečka, pásik životov bossa, skóre počas hry, „+50“ nad zásahmi.
- Obrazovka konca hry s rozpisom skóre a **ukladaním najlepšieho skóre** (`highscore.json`).
- Zvukové efekty.

## Opravené chyby z pôvodného kódu
- Argumenty do `main()` sa posielali v zlom poradí (prehodené `next_boss_move` a prahové časy).
- `kill_score` sa pripočítaval každý snímok, kým mal boss 0 životov.
- Pohyb šikmo používal `PLAYER_VEL - 6` (= −1), takže bol pomalší/nerovnomerný.
- Mazanie striel zo zoznamu počas prechádzania cez ten istý zoznam (niektoré strely sa preskočili).
- `pygame.time.delay()` zamrazil okno na začiatku aj na konci hry – teraz odpočet a interaktívna obrazovka.
- `FONT.render(..., WIDTH)` – farba textu bola číslo 1000 namiesto farby.
