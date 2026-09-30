"""Ikony a aktuálne ceny z valorant-api.com (neoficiálne, verejné a zadarmo).

Sťahovanie beží na pozadí, obrázky sa ukladajú do priečinka cache/, takže
po prvom spustení fungujú aj bez internetu. Bez internetu sa namiesto ikon
zobrazí len text.
"""

import hashlib
import json
import os
import threading
import time
import urllib.request

try:
    from PIL import Image, ImageTk
except ImportError:  # Pillow je voliteľný
    Image = ImageTk = None

import tkinter as tk

import udaje as U

API = "https://valorant-api.com/v1/"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
MAX_AGE = 3 * 24 * 3600  # údaje z API obnoví raz za 3 dni


def _download(url, path, timeout=10):
    request = urllib.request.Request(url, headers={"User-Agent": "valorant-stats"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read()
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


class IconStore:
    def __init__(self):
        os.makedirs(os.path.join(CACHE, "img"), exist_ok=True)
        self.agents = {}     # meno -> {"icon", "role", "abilities": {slot: (názov, ikona)}}
        self.weapons = {}    # meno -> {"icon", "cost", "category"}
        self.shields = {}    # light/regen/heavy -> {"icon", "cost", "name"}
        self.ready = False
        self.status = "Načítavam údaje z valorant-api.com…"
        self.version = 0     # zvýši sa, keď pribudnú ikony (okná sa prekreslia)
        self._photos = {}
        self._lock = threading.Lock()

    # Načítanie na pozadí #

    def start(self):
        threading.Thread(target=self._load_all, daemon=True).start()

    def _json(self, name, url):
        path = os.path.join(CACHE, name + ".json")
        fresh = os.path.exists(path) and time.time() - os.path.getmtime(path) < MAX_AGE
        if not fresh:
            try:
                _download(url, path)
            except Exception:
                pass  # bez internetu použijeme starú kópiu, ak existuje
        with open(path, encoding="utf-8") as f:
            return json.load(f)["data"]

    def _load_all(self):
        try:
            for agent in self._json("agents", API + "agents?isPlayableCharacter=true&language=en-US"):
                abilities = {a.get("slot"): (a.get("displayName"), a.get("displayIcon")) for a in agent.get("abilities", [])}
                role = (agent.get("role") or {}).get("displayName")
                self.agents[agent["displayName"]] = {"icon": agent.get("displayIcon"), "role": role,
                                                     "abilities": abilities}
            for weapon in self._json("weapons", API + "weapons?language=en-US"):
                shop = weapon.get("shopData") or {}
                self.weapons[weapon["displayName"]] = {"icon": weapon.get("displayIcon"),
                                                       "cost": shop.get("cost", 0),
                                                       "category": shop.get("category", "")}
            for gear in self._json("gear", API + "gear?language=en-US"):
                name = gear.get("displayName", "")
                for key in ("light", "regen", "heavy"):
                    if key in name.lower():
                        self.shields[key] = {"icon": gear.get("displayIcon"), "name": name,
                                             "cost": (gear.get("shopData") or {}).get("cost")}
            self.status = f"Údaje z API načítané ({len(self.agents)} agentov, {len(self.weapons)} zbraní)."
        except Exception as error:
            self.status = f"API nedostupné – beží bez ikon ({error.__class__.__name__})."
            return
        self.ready = True
        self.version += 1

        # Stiahnutie obrázkov, ktoré program používa #
        urls = [a["icon"] for a in self.agents.values()]
        urls += [w["icon"] for w in self.weapons.values()]
        urls += [s["icon"] for s in self.shields.values()]
        for agent in U.MY_AGENTS:
            urls += [icon for _, icon in self.agents.get(agent, {}).get("abilities", {}).values()]
        for url in urls:
            if url and not os.path.exists(self._path(url)):
                try:
                    _download(url, self._path(url))
                except Exception:
                    continue
        self.version += 1

    # Ceny a role z API #

    def update_prices(self, prices):
        for name, info in self.weapons.items():
            if name in prices["weapons"] and info.get("cost") is not None:
                prices["weapons"][name] = (info["cost"], prices["weapons"][name][1])
        for key, info in self.shields.items():
            if info.get("cost"):
                prices["shields"][key] = info["cost"]

    def roles(self):
        roles = dict(U.ROLES)
        for name, info in self.agents.items():
            if info.get("role"):
                roles[name] = info["role"]
        return roles

    # Obrázky pre tkinter #

    def _path(self, url):
        return os.path.join(CACHE, "img", hashlib.md5(url.encode()).hexdigest() + ".png")

    def _url(self, kind, name, slot=None):
        if kind == "agent":
            return self.agents.get(name, {}).get("icon")
        if kind == "weapon":
            return self.weapons.get(name, {}).get("icon")
        if kind == "shield":
            return self.shields.get(name, {}).get("icon")
        if kind == "ability":
            return self.agents.get(name, {}).get("abilities", {}).get(slot, (None, None))[1]
        return None

    def photo(self, kind, name, height, slot=None, max_width=None):
        """Vráti obrázok pre tkinter (alebo None, ak ešte nie je stiahnutý)."""
        url = self._url(kind, name, slot)
        if not url:
            return None
        key = (url, height, max_width)
        if key in self._photos:
            return self._photos[key]
        path = self._path(url)
        if not os.path.exists(path):
            return None
        try:
            if Image:
                image = Image.open(path).convert("RGBA")
                bbox = image.getbbox()
                if bbox:
                    image = image.crop(bbox)
                w, h = image.size
                scale = height / h
                if max_width and w * scale > max_width:
                    scale = max_width / w
                image = image.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
                photo = ImageTk.PhotoImage(image)
            else:
                photo = tk.PhotoImage(file=path)
                factor = max(1, photo.height() // max(1, height))
                photo = photo.subsample(factor, factor)
        except Exception:
            return None
        self._photos[key] = photo
        return photo
