# 💗 Pre Dominiku

Malá stránka s láskou pre Dominiku. Jeden súbor `index.html`, žiadna inštalácia.

## Čo na nej je
- **Srdiečko** – klikni naň a povie ti niečo milé.
- **Pohárik lásky** – každý deň jeden nový lístok (oplatí sa vracať každý deň).
- **Otvor, keď…** – listy na smutné chvíle, keď nemôže zaspať, keď sa hnevá…
- **Kupóny lásky** – skutočné kupóny (masáž, raňajky do postele, výhra v hádke…).
  Po uplatnení sa kupón označí a pošle sa ti správa.

## Prispôsobenie
Na začiatku `<script>` v `index.html` je blok `CONFIG`:
- `spoluOd` – dátum, odkedy ste spolu (napr. `"2019-06-14"`) → zobrazí počítadlo dní
- `svadba` – dátum svadby → počítadlo dní manželstva
- `podpis` – podpis pod listami

Polia `NOTES`, `LETTERS` a `COUPONS` môžeš ľubovoľne upraviť – najlepšie fungujú vlastné spomienky a vtipy, ktoré poznáte len vy dvaja.

## Zverejnenie (GitHub Pages)
Settings → Pages → Source: *Deploy from a branch* → vyber vetvu a priečinok `/ (root)`.
Po chvíli bude stránka na `https://<tvoj-účet>.github.io/domini/`.
