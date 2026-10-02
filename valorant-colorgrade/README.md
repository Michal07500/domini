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

## Discord / OBS / klipy

Vibrance a kontrast sa menia až na výstupe do monitora. **Discord, OBS ani nahrávanie to nezachytia**, tie dostanú obraz ešte pred touto úpravou. Ľudia na Discorde preto uvidia normálne farby.

Aby to videli aj oni, farby treba upraviť priamo v obraze, ktorý zdieľaš. Najjednoduchšie je to cez bezplatný OBS:

1. V OBS pridaj zdroj **Game Capture** (Valorant) alebo **Display Capture** (hlavný monitor).
2. Klikni na zdroj pravým tlačidlom → **Filters** → **+** → **Color Correction**. Ako štart nastav:
   - Saturation **0.5**
   - Contrast **0.1**
   - Gamma **0.05**

   Potom dolaď podľa oka, aby to vyzeralo ako na tvojom monitore.
3. Klikni pravým tlačidlom do náhľadu v OBS → **Windowed Projector (Preview)**. Otvorí sa okno s upraveným obrazom. Daj ho na druhý monitor.
4. V Discorde daj **Share Screen** → **Applications** a vyber okno **Windowed Projector**.

Tento program si nechaj zapnutý tiež, aby si ten look videl aj ty na hlavnom monitore. Ten istý OBS filter sa použije aj na nahrávanie klipov, takže aj tie budú farebné.

ReShade ani podobné „injektory“ do hry nepoužívaj. Vanguard ich blokuje a hrozí ban.
