"""Malé okno (overlay) nad hrou – ukazuje, čo si má hráč kúpiť.

Ťahaním myšou sa presúva, rohom vpravo dole sa mení veľkosť,
pravým tlačidlom sa otvorí menu (priehľadnosť, veľkosť písma, skryť).
Funguje nad hrou, ak má Valorant režim "Windowed Fullscreen" (nie čisté Fullscreen).
"""

import sys
import tkinter as tk

BG = "#0f1923"
PANEL = "#1b2733"
TEXT = "#ece8e1"
MUTED = "#8b99a6"
RED = "#ff4655"
GREEN = "#3fd6a0"
GOLD = "#f5c542"

TIER_COLORS = {"Full buy": GREEN, "Overtime": GREEN, "Bonus kolo": GOLD, "Half buy": GOLD, "Force buy": RED,
               "All-in": RED, "Eco": MUTED, "Pistolové kolo": GOLD}


class Overlay(tk.Toplevel):
    def __init__(self, master, icons, settings, on_change):
        super().__init__(master)
        self.icons = icons
        self.settings = settings
        self.on_change = on_change  # uloží nastavenia
        self.data = {"mode": "waiting", "text": "Začni zápas v hlavnom okne"}
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", settings["overlay_alpha"])
        self.configure(bg=RED)  # tenký červený rámik
        self.geometry(settings["overlay_geometry"] or "400x240+1500+60")

        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True, padx=2, pady=2)
        self.grip = tk.Label(self, text="◢", bg=BG, fg=MUTED, cursor="size_nw_se" if sys.platform == "win32" else "bottom_right_corner", font=("Segoe UI", 9))
        self.grip.place(relx=1, rely=1, anchor="se", x=-2, y=-2)
        self.grip.bind("<ButtonPress-1>", self._start_resize)
        self.grip.bind("<B1-Motion>", self._resize)
        self.grip.bind("<ButtonRelease-1>", lambda e: self._save_geometry())

        self.menu = tk.Menu(self, tearoff=0, bg=PANEL, fg=TEXT, activebackground=RED)
        self.menu.add_command(label="Priehľadnejšie", command=lambda: self.change_alpha(-0.1))
        self.menu.add_command(label="Menej priehľadné", command=lambda: self.change_alpha(0.1))
        self.menu.add_separator()
        self.menu.add_command(label="Väčšie písmo", command=lambda: self.change_scale(0.1))
        self.menu.add_command(label="Menšie písmo", command=lambda: self.change_scale(-0.1))
        self.menu.add_separator()
        self.menu.add_command(label="Skryť overlay", command=self.hide)
        self._last_width = 0
        self.bind("<Configure>", self._on_configure)
        self.render()

    # Presúvanie a zmena veľkosti #

    def _bind_drag(self, widget):
        widget.bind("<ButtonPress-1>", self._start_move)
        widget.bind("<B1-Motion>", self._move)
        widget.bind("<ButtonRelease-1>", lambda e: self._save_geometry())
        widget.bind("<Button-3>", lambda e: self.menu.tk_popup(e.x_root, e.y_root))

    def _start_move(self, event):
        self._drag = (event.x_root - self.winfo_x(), event.y_root - self.winfo_y())

    def _move(self, event):
        self.geometry(f"+{event.x_root - self._drag[0]}+{event.y_root - self._drag[1]}")

    def _start_resize(self, event):
        self._size = (event.x_root, event.y_root, self.winfo_width(), self.winfo_height())

    def _resize(self, event):
        x0, y0, w0, h0 = self._size
        w = max(200, w0 + event.x_root - x0)
        h = max(120, h0 + event.y_root - y0)
        self.geometry(f"{w}x{h}")

    def _on_configure(self, event):
        if event.widget is self and abs(event.width - self._last_width) > 20:
            self._last_width = event.width
            self.render()

    def _save_geometry(self):
        self.settings["overlay_geometry"] = self.geometry()
        self.on_change()

    def change_alpha(self, delta):
        alpha = max(0.3, min(1.0, self.settings["overlay_alpha"] + delta))
        self.settings["overlay_alpha"] = alpha
        self.attributes("-alpha", alpha)
        self.on_change()

    def change_scale(self, delta):
        self.settings["overlay_scale"] = max(0.6, min(2.0, round(self.settings["overlay_scale"] + delta, 1)))
        self.render()
        self.on_change()

    def hide(self):
        self.settings["overlay_visible"] = False
        self.withdraw()
        self.on_change()

    def show_window(self):
        self.settings["overlay_visible"] = True
        self.deiconify()
        self.attributes("-topmost", True)
        self.on_change()

    # Obsah #

    def show(self, data):
        self.data = data
        self.render()

    def _label(self, parent, text, size, color=TEXT, bold=False, **pack):
        s = self.settings["overlay_scale"]
        label = tk.Label(parent, text=text, bg=BG, fg=color, font=("Segoe UI", int(size * s), "bold" if bold else "normal"),
                         justify="left", wraplength=max(150, self.winfo_width() - 20))
        label.pack(**({"anchor": "w"} | pack))
        self._bind_drag(label)
        return label

    def _image(self, parent, photo, text, side="left"):
        label = tk.Label(parent, image=photo, text=text, compound="top" if photo else "none", bg=BG, fg=TEXT,
                         font=("Segoe UI", int(8 * self.settings["overlay_scale"])))
        label.image = photo
        label.pack(side=side, padx=4)
        self._bind_drag(label)
        return label

    def render(self):
        for child in self.body.winfo_children():
            child.destroy()
        self._bind_drag(self.body)
        s = self.settings["overlay_scale"]
        pad = tk.Frame(self.body, bg=BG)
        pad.pack(fill="both", expand=True, padx=8, pady=6)
        self._bind_drag(pad)
        data = self.data

        if data["mode"] == "waiting":
            self._label(pad, "VALORANT STATS", 9, RED, True)
            self._label(pad, data["text"], 11)
            return

        if data["mode"] == "agent":
            self._label(pad, "ODPORÚČANÝ AGENT", 9, RED, True)
            row = tk.Frame(pad, bg=BG)
            row.pack(anchor="w", pady=2)
            self._bind_drag(row)
            self._image(row, self.icons.photo("agent", data["agent"], int(44 * s)), "")
            self._label(row, f"{data['agent']}  ({data['confidence']})", 15, TEXT, True, side="left")
            for reason in data.get("reasons", [])[:3]:
                self._label(pad, "• " + reason, 9, MUTED)
            return

        # Nákup #
        header = tk.Frame(pad, bg=BG)
        header.pack(fill="x")
        self._bind_drag(header)
        self._label(header, f"KOLO {data['round']}  •  {data['score']}", 9, MUTED, True, side="left")
        self._label(header, data["tier"].upper(), 10, TIER_COLORS.get(data["tier"], TEXT), True, side="right",
                    anchor="e")

        items = tk.Frame(pad, bg=BG)
        items.pack(anchor="w", pady=(4, 2))
        self._bind_drag(items)
        weapon_photo = self.icons.photo("weapon", data["weapon"], int(34 * s), max_width=int(120 * s))
        self._image(items, weapon_photo, data["weapon"] if weapon_photo else data["weapon"].upper())
        if data["shield"] != "none":
            shield_photo = self.icons.photo("shield", data["shield"], int(30 * s))
            self._image(items, shield_photo, data["shield_name"])
        for slot, name, count, _ in data["abilities"]:
            photo = self.icons.photo("ability", data["agent"], int(26 * s), slot=slot)
            self._image(items, photo, name + (f" ×{count}" if count > 1 else ""))

        self._label(pad, f"Spolu {data['cost']}  •  zostane {data['credits_left']}", 10, TEXT, True)
        self._label(pad, f"Ak prehráte: {data['next_if_loss']}   Ak vyhráte: {data['next_if_win']}", 9, MUTED)
        if data.get("tip"):
            self._label(pad, data["tip"], 9, GOLD)
