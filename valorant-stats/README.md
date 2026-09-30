# Valorant Stats

Poradca pre Valorant v Pythone. Program má **veľké okno** (na ľavý monitor) a **malý overlay** (na pravý monitor, nad hru).

- Podľa agentov spoluhráčov (stačí zadať tých, ktorých poznáš) a mapy odporučí, či hrať **Reynu alebo Breacha**, a vysvetlí prečo.
- Na **pistolové kolo** a potom na **každé kolo** poradí, čo kúpiť: zbraň, štít a schopnosti, aj s ikonami.
- Učí sa z tvojich zápasov: ktorá zbraň ti ide (napríklad Vandal alebo Phantom), či sa ti oplácajú force buye a ako ti ide Reyna a Breach.
- Má **históriu** zápasov a kôl a **analýzu** s grafmi.

## Spustenie (Windows)
1. Nainštaluj Python z https://www.python.org/downloads/ a zaškrtni „Add Python to PATH“.
2. ZIP s projektom **rozbaľ** (pravý klik → Extrahovať všetko…).
3. V priečinku `valorant-stats` dvakrát klikni na **`spustit.bat`**. Pri prvom spustení doinštaluje knižnice a potom spustí program.

Ručne sa dá spustiť aj takto:
```
pip install -r requirements.txt
python valorant_stats.py
```
Bez knižníc (`pillow`, `mss`, `pytesseract`) program tiež funguje. Ikony sú však kvalitnejšie s Pillow a OCR bez týchto knižníc nefunguje.

## Ako sa používa
1. **Záložka ZÁPAS vľavo**: vyber mapu a agentov spoluhráčov. Karta Reyna/Breach sa hneď prepočíta. Klikni **Hrám Reynu** alebo **Hrám Breacha**.
2. **Kolo 1**: kredity sa vyplnia samé (800). Klikni **Odporučiť nákup** (alebo stlač Enter). Keď nakúpiš, klikni **✔ Kúpil som to**. Ak si kúpil niečo iné, vyber to a klikni **Uložiť**.
3. **Každé ďalšie kolo** vyplň:
   - **Minulé kolo**: či ste ho vyhrali alebo prehrali,
   - **K / D / A**: celkové čísla zo scoreboardu (Tab); program si sám dopočíta, koľko to bolo v poslednom kole,
   - **Kredity**,
   - voliteľne čo ti **zostalo** (ak si prežil so zbraňou alebo štítom) a **plán tímu**.
4. Na konci klikni **Ukončiť zápas** a zápas sa uloží do histórie. Program sa podľa neho doučí. Keď niekto dosiahne 13, program sa na koniec zápasu opýta sám.

Program sleduje skóre, sériu prehier (loss bonus 1900/2400/2900), polčas (kolo 13 je znova pistolové kolo), overtime (5000 kreditov) aj posledné kolo polčasu, keď treba minúť všetko. Počíta aj s tým, koľko budeš mať v ďalšom kole, keď kolo prehráte.

## Overlay
- **Ťahaním** ho presunieš, **rohom vpravo dole** zmeníš veľkosť a **pravým tlačidlom** otvoríš menu (priehľadnosť, písmo, skryť).
- Pozíciu a veľkosť si pamätá. V Nastaveniach sú tlačidlá **Hlavné okno na ľavý monitor** a **Overlay na pravý monitor**.
- Aby bol overlay nad hrou, nastav vo Valorante **Video → General → Display Mode: Windowed Fullscreen**. V čistom Fullscreen režime ho hra prekryje.

## Ako sa učí
Každé kolo sa uloží: typ nákupu, zbraň, či ste vyhrali a koľko si mal killov. Z toho program počíta:
- percento vyhratých kôl a killy za kolo pre každú zbraň,
- úspešnosť typov nákupu (eco, force, full…),
- percento výhier a K/D na Reyne a Breachovi.

Kým je dát málo, drží sa bežných odporúčaní. Čím viac zápasov odohráš, tým viac sa prispôsobí tvojim výsledkom, takže jedno šťastné kolo ho nepokazí. Čo sa zatiaľ naučil, vidíš v záložke **Analýza**.

## Ikony a ceny
Ikony agentov, zbraní, štítov a schopností aj aktuálne ceny zbraní sa sťahujú z verejného [valorant-api.com](https://valorant-api.com) a ukladajú do `cache/`, takže potom fungujú aj offline.
**Ceny schopností** API neposkytuje, sú v `udaje.py` (Reyna: Leer 250, Devour/Dismiss 100; Breach: Flashpoint 250, Aftershock 200). Ak ich Riot zmení, uprav ich tam.

## OCR – automatické čítanie kreditov (experimentálne)
Dá sa to spraviť. Program si každé 2 sekundy odfotí malý výrez obrazovky, kde hra ukazuje kredity, a prečíta z neho číslo.
1. `pip install mss pytesseract pillow`
2. Nainštaluj **Tesseract OCR**: https://github.com/UB-Mannheim/tesseract/wiki (predvolená cesta `C:\Program Files\Tesseract-OCR\tesseract.exe`).
3. V hre otvor nákupné menu. V programe choď do **Nastavenia → Vybrať oblasť s kreditmi** a myšou označ obdĺžnik tesne okolo čísla kreditov.
4. Klikni **Otestovať** a potom zapni **Čítať automaticky**.

OCR len číta obraz na monitore. Do hry, jej súborov ani pamäte nezasahuje. Riot však takéto pomocné nástroje oficiálne nepodporuje, preto ho používaš na vlastné riziko.
Výsledok kola a K/D/A sa cez OCR zatiaľ nečítajú, lebo sú na obrazovke len krátko a na rôznych miestach. Zadávaš ich ručne.

**Nápad do budúcna:** agentov spoluhráčov by šlo brať automaticky z lokálneho API Riot klienta, ktoré používajú napríklad niektoré „rank checkery“. Je to však neoficiálne a Riot to môže kedykoľvek zmeniť, preto to zatiaľ nie je zapnuté.

## Súbory
| Súbor | Čo obsahuje |
|---|---|
| `valorant_stats.py` | hlavné okno a záložky Zápas, História, Analýza, Nastavenia |
| `overlay.py` | malé okno nad hrou |
| `logika.py` | odporúčanie agenta, nákupu a učenie z histórie |
| `udaje.py` | role agentov, ceny, ekonomika, mapy (dá sa upravovať) |
| `ikony.py` | sťahovanie ikon a cien z valorant-api.com |
| `ocr.py` | čítanie kreditov z obrazovky |
| `grafy.py` | grafy v záložke Analýza |
| `ukladanie.py` | ukladanie do `moje_data/` (história, rozohraný zápas, nastavenia) |
| `test_logika.py` | testy: `python -m unittest test_logika.py` |
