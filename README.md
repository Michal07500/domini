# 💗 Pre Dominiku

Malá pixelová stránka pre Dominiku. Jeden súbor `index.html`, žiadna inštalácia, funguje na mobile aj na počítači.

## Čo na nej je
- **Pixelové srdiečko** – klikni naň a povie ti niečo milé.
- **Mačacia izbička** – pixelové mačičky sa prechádzajú, spia, žmurkajú a vrtia chvostíkmi.
  Pohladkaj mačičku a pošepká ti kompliment. Ťukni na zem → klbko, tlačidlo → rybky. Dá sa pridať ďalšia mačička.
- **Super Dominika** – 2D pixelová skákačka: zbieraj srdiečka, búchaj do **?** kociek, skáč brokoliciam na hlavu a dostaň sa k zámku 👑.
  Na mobile sú tlačidlá na obrazovke, na počítači šípky + medzerník.
- **Origami srdiečko** – 3D animovaný návod krok za krokom (10 krokov), model sa dá prstom otáčať.
- **Otázka na konci** – tlačidlo „NIE“ pred ňou uteká 😏 Po „ÁNO“ ti môže poslať správu.

## Prispôsobenie
Na začiatku `<script>` v `index.html` je blok `CONFIG`:
- `poznameSaOd` – dátum, odkedy sa poznáte (napr. `"2024-09-02"`) → zobrazí počítadlo dní
- `podpis` – podpis v pätičke
- `otazka` – otázka na konci stránky (predvolene „Pôjdeš so mnou na kávu? ☕“)

Pole `NOTES` (čo šepkajú mačičky) môžeš ľubovoľne upraviť – najlepšie fungujú vlastné spomienky a vtipy, ktoré poznáte len vy dvaja.

## Zverejnenie (GitHub Pages)
Settings → Pages → Source: *Deploy from a branch* → vyber vetvu a priečinok `/ (root)`.
Po chvíli bude stránka na `https://<tvoj-účet>.github.io/domini/`.
