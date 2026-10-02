# Valorant Color Grade

Malý program pre Windows: **kým je spustený, hra (aj celá obrazovka) má farebnejší color grade. Keď ho zavrieš, všetko sa vráti presne tak, ako to bolo.**

## Použitie

1. Stiahni priečinok `valorant-colorgrade` (oba súbory musia byť spolu).
2. Dvojklik na **`Spustit ColorGrade.bat`** → otvorí sa malé okno „COLOR GRADE: ZAPNUTÝ“.
3. Hraj Valorant.
4. Po hraní zavri okno (X) → farby sa vrátia späť.

Netreba nič inštalovať, používa iba PowerShell, ktorý je vo Windows.

## Čo program mení

| Posuvník | Čo robí | Predvolené |
|---|---|---|
| Vibrance | NVIDIA „Digital Vibrance“ (sýtosť farieb), rovnaké číslo ako v NVIDIA Control Panel | 80 |
| Kontrast | Výraznejšie svetlá a tiene | 110 % |
| Gamma | Nad 100 svetlejšie, pod 100 tmavšie | 100 |
| Jas | Jemné posunutie jasu | 0 |

Zmeny na posuvníkoch sa uložia, takže nabudúce sa spustí rovnaký look.

## Dobré vedieť

- **Vibrance funguje iba na NVIDIA kartách.** Na AMD/Intel program zmení iba kontrast, gammu a jas (sýtosť nastav v AMD Software).
- Ak Windows odmietne veľmi silnú krivku, okno to napíše. Stačí znížiť kontrast alebo gammu.
- Ak by program spadol alebo by sa vypol počítač, pri ďalšom spustení najprv vráti pôvodné farby.
- Program nesiaha do hry, mení iba nastavenia ovládača a monitora (ako NVIDIA Control Panel alebo VibranceGUI).
