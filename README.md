# 💗 Pre Dominiku

Malá stránka s láskou pre Dominiku. Jeden súbor `index.html`, žiadna inštalácia.

## Čo na nej je
- **Srdiečko** – klikni naň a povie ti niečo milé.
- **Pohárik úsmevov** – každý deň jeden nový lístok (oplatí sa vracať každý deň).
- **Hra „Chyť srdiečka“** – 30 sekúnd, chytaj 💗 🧁 ⭐ a vyhýbaj sa 🌧️ 🥦. Rekord sa pamätá a skóre ti môže poslať.
- **Otvor, keď…** – listy na smutné chvíle, na nudu, na stres, keď nemôže zaspať…
- **Kupóny** – skutočné kupóny (káva, zmrzlina, pizza, výhra v hádke…).
  Po uplatnení sa kupón označí a pošle sa ti správa.
- **Otázka na konci** – tlačidlo „Nie“ pred ňou uteká 😏 Po „Áno“ ti môže poslať správu.

## Prispôsobenie
Na začiatku `<script>` v `index.html` je blok `CONFIG`:
- `poznameSaOd` – dátum, odkedy sa poznáte (napr. `"2024-09-02"`) → zobrazí počítadlo dní
- `podpis` – podpis pod listami
- `otazka` – otázka na konci stránky (predvolene „Pôjdeš so mnou na kávu? ☕“)

Polia `NOTES`, `LETTERS` a `COUPONS` môžeš ľubovoľne upraviť – najlepšie fungujú vlastné spomienky a vtipy, ktoré poznáte len vy dvaja.

## Zverejnenie (GitHub Pages)
Settings → Pages → Source: *Deploy from a branch* → vyber vetvu a priečinok `/ (root)`.
Po chvíli bude stránka na `https://<tvoj-účet>.github.io/domini/`.
