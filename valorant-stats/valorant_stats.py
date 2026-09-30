"""VALORANT STATS – poradca na výber agenta a nákup v každom kole.

Spustenie:  python valorant_stats.py
Hlavné okno daj na ľavý monitor, malý overlay na pravý (nad hru).
"""

import datetime
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
if not os.path.exists(os.path.join(HERE, "logika.py")):
    print("CHYBA: Chýbajú ostatné súbory programu. Asi si ho spustil priamo zo ZIP-u –")
    print("klikni na ZIP pravým tlačidlom -> 'Extrahovať všetko...' a spusti ho z rozbaleného priečinka.")
    input("Stlač Enter na ukončenie...")
    sys.exit(1)

import grafy
import logika as L
import ocr
import udaje as U
import ukladanie as S
from ikony import IconStore
from overlay import Overlay

# Farby (štýl Valorantu) #
BG = "#0f1923"
PANEL = "#1b2733"
PANEL2 = "#243442"
LINE = "#2f4254"
TEXT = "#ece8e1"
MUTED = "#8b99a6"
RED = "#ff4655"
GREEN = "#3fd6a0"
GOLD = "#f5c542"
BLUE = "#58a6ff"
FONT = "Segoe UI"


def enable_dpi_awareness():
    # Na Windows s mierkou 125 %+ by inak bol text rozmazaný a OCR by bralo zlé súradnice #
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def virtual_screen(root):
    """Rozmery celej plochy cez všetky monitory: (x, y, šírka, výška)."""
    try:
        import ctypes
        u = ctypes.windll.user32
        return u.GetSystemMetrics(76), u.GetSystemMetrics(77), u.GetSystemMetrics(78), u.GetSystemMetrics(79)
    except Exception:
        return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def button(parent, text, command, color=RED, fg=TEXT, **kw):
    b = tk.Button(parent, text=text, command=command, bg=color, fg=fg, activebackground=TEXT,
                  activeforeground=BG, relief="flat", bd=0, padx=14, pady=6, cursor="hand2",
                  font=(FONT, 10, "bold"), **kw)
    return b


def card(parent, title):
    frame = tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground=LINE)
    tk.Label(frame, text=title.upper(), bg=PANEL, fg=RED, font=(FONT, 10, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
    body = tk.Frame(frame, bg=PANEL)
    body.pack(fill="both", expand=True, padx=12, pady=(0, 12))
    return frame, body


def label(parent, text="", size=10, color=TEXT, bold=False, bg=PANEL, **kw):
    return tk.Label(parent, text=text, bg=bg, fg=color, font=(FONT, size, "bold" if bold else "normal"),
                    justify="left", **kw)


class App:
    def __init__(self):
        enable_dpi_awareness()
        self.root = tk.Tk()
        self.root.title("Valorant Stats")
        self.root.configure(bg=BG)
        self.settings = S.load_settings()
        self.root.geometry(self.settings["main_geometry"])
        self.root.minsize(1000, 680)
        self.style()

        self.history = S.load_history()
        self.profile = L.Profile(self.history)
        self.prices = L.default_prices()
        self.icons = IconStore()
        self.icons.start()
        self.icon_version = -1

        self.match = S.load_current()
        self.agent_result = None
        self.buy = None
        self.ocr_job = None

        self.overlay = Overlay(self.root, self.icons, self.settings, self.save_settings)
        if not self.settings["overlay_visible"]:
            self.overlay.withdraw()
        if not self.settings["overlay_geometry"]:
            self.place_overlay_right()

        self.build()
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.bind("<Return>", lambda e: self.recommend_buy() if self.match and self.match.get("agent") else None)
        self.poll_icons()
        if self.settings["ocr_auto"]:
            self.toggle_ocr_auto(True)

    # # # VZHĽAD # # #

    def style(self):
        s = ttk.Style(self.root)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=TEXT, fieldbackground=PANEL2, bordercolor=LINE,
                    lightcolor=PANEL2, darkcolor=PANEL2, font=(FONT, 10))
        s.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(10, 8, 10, 0))
        s.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(18, 8), font=(FONT, 10, "bold"),
                    borderwidth=0)
        s.map("TNotebook.Tab", background=[("selected", RED)], foreground=[("selected", TEXT)])
        s.configure("TCombobox", fieldbackground=PANEL2, background=PANEL2, foreground=TEXT, arrowcolor=TEXT,
                    selectbackground=PANEL2, selectforeground=TEXT, padding=4)
        s.map("TCombobox", fieldbackground=[("readonly", PANEL2)], foreground=[("readonly", TEXT)])
        s.configure("TSpinbox", fieldbackground=PANEL2, foreground=TEXT, arrowcolor=TEXT, padding=4)
        s.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=26,
                    borderwidth=0)
        s.configure("Treeview.Heading", background=PANEL2, foreground=MUTED, font=(FONT, 9, "bold"), relief="flat")
        s.map("Treeview", background=[("selected", RED)])
        s.configure("TCheckbutton", background=PANEL, foreground=TEXT)
        s.configure("TRadiobutton", background=PANEL, foreground=TEXT)
        s.map("TCheckbutton", background=[("active", PANEL)])
        s.map("TRadiobutton", background=[("active", PANEL)])
        s.configure("Horizontal.TScale", background=PANEL, troughcolor=PANEL2)
        self.root.option_add("*TCombobox*Listbox.background", PANEL2)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", RED)
        self.root.option_add("*TCombobox*Listbox.font", (FONT, 10))

    def build(self):
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=16, pady=(12, 0))
        tk.Label(top, text="VALORANT", bg=BG, fg=RED, font=(FONT, 20, "bold")).pack(side="left")
        tk.Label(top, text=" STATS", bg=BG, fg=TEXT, font=(FONT, 20, "bold")).pack(side="left")
        self.api_label = label(top, "", 9, MUTED, bg=BG)
        self.api_label.pack(side="right")
        button(top, "Overlay zobraziť/skryť", self.toggle_overlay, PANEL2).pack(side="right", padx=8)

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=8, pady=8)
        self.tab_match = tk.Frame(self.tabs, bg=BG)
        self.tab_history = tk.Frame(self.tabs, bg=BG)
        self.tab_analysis = tk.Frame(self.tabs, bg=BG)
        self.tab_settings = tk.Frame(self.tabs, bg=BG)
        self.tabs.add(self.tab_match, text="ZÁPAS")
        self.tabs.add(self.tab_history, text="HISTÓRIA")
        self.tabs.add(self.tab_analysis, text="ANALÝZA")
        self.tabs.add(self.tab_settings, text="NASTAVENIA")
        self.tabs.bind("<<NotebookTabChanged>>", lambda e: self.refresh_tab())

        self.build_match_tab()
        self.build_history_tab()
        self.build_analysis_tab()
        self.build_settings_tab()
        self.refresh_match()

    # # # ZÁLOŽKA: ZÁPAS # # #

    def build_match_tab(self):
        t = self.tab_match
        t.columnconfigure(0, weight=5, uniform="c")
        t.columnconfigure(1, weight=7, uniform="c")
        t.rowconfigure(0, weight=1)
        left = tk.Frame(t, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(8, 6), pady=8)
        right = tk.Frame(t, bg=BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 8), pady=8)

        # 1. Tím #
        frame, body = card(left, "1. Tím a agent")
        frame.pack(fill="both", expand=True)
        row = tk.Frame(body, bg=PANEL)
        row.pack(fill="x", pady=2)
        label(row, "Mapa", 10, MUTED, width=12, anchor="w").pack(side="left")
        self.map_var = tk.StringVar(value="Neviem")
        box = ttk.Combobox(row, textvariable=self.map_var, values=list(U.MAPS), state="readonly", width=18)
        box.pack(side="left")
        box.bind("<<ComboboxSelected>>", lambda e: self.recommend_agent())

        label(body, "Agenti spoluhráčov (vyplň, koho poznáš):", 10, MUTED).pack(anchor="w", pady=(10, 4))
        self.mate_vars, self.mate_icons, self.mate_boxes = [], [], []
        for i in range(4):
            row = tk.Frame(body, bg=PANEL)
            row.pack(fill="x", pady=2)
            icon = tk.Label(row, bg=PANEL, width=4)
            icon.pack(side="left")
            var = tk.StringVar()
            combo = ttk.Combobox(row, textvariable=var, state="readonly", width=20)
            combo.pack(side="left", padx=6)
            combo.bind("<<ComboboxSelected>>", lambda e: self.recommend_agent())
            role = label(row, "", 9, MUTED)
            role.pack(side="left")
            self.mate_vars.append(var)
            self.mate_icons.append((icon, role))
            self.mate_boxes.append(combo)
        self.update_agent_lists()

        self.agent_cards = tk.Frame(body, bg=PANEL)
        self.agent_cards.pack(fill="both", expand=True, pady=(12, 0))
        self.agent_notes = label(body, "", 9, GOLD, wraplength=420)
        self.agent_notes.pack(anchor="w", pady=4)
        buttons = tk.Frame(body, bg=PANEL)
        buttons.pack(fill="x")
        button(buttons, "Hrám Reynu", lambda: self.start_match("Reyna")).pack(side="left")
        button(buttons, "Hrám Breacha", lambda: self.start_match("Breach")).pack(side="left", padx=8)

        # 2. Kolo #
        frame, body = card(right, "2. Kolo a nákup")
        frame.pack(fill="both", expand=True)
        self.round_header = label(body, "", 13, TEXT, True)
        self.round_header.pack(anchor="w")
        self.round_sub = label(body, "", 9, MUTED)
        self.round_sub.pack(anchor="w", pady=(0, 6))

        form = tk.Frame(body, bg=PANEL)
        form.pack(fill="x")
        self.result_var = tk.StringVar(value="")
        self.result_row = tk.Frame(form, bg=PANEL)
        self.result_row.grid(row=0, column=0, columnspan=4, sticky="w", pady=3)
        label(self.result_row, "Minulé kolo", 10, MUTED, width=16, anchor="w").pack(side="left")
        ttk.Radiobutton(self.result_row, text="Vyhrali sme", value="win", variable=self.result_var).pack(side="left")
        ttk.Radiobutton(self.result_row, text="Prehrali sme", value="loss", variable=self.result_var).pack(side="left", padx=10)

        label(form, "Moje K / D / A", 10, MUTED, width=16, anchor="w").grid(row=1, column=0, sticky="w", pady=3)
        kda = tk.Frame(form, bg=PANEL)
        kda.grid(row=1, column=1, columnspan=3, sticky="w")
        self.kda_vars = [tk.IntVar(value=0) for _ in range(3)]
        for var in self.kda_vars:
            ttk.Spinbox(kda, from_=0, to=99, textvariable=var, width=4).pack(side="left", padx=(0, 6))
        label(kda, "(čísla zo scoreboardu – celkové)", 8, MUTED).pack(side="left")

        label(form, "Kredity", 10, MUTED, width=16, anchor="w").grid(row=2, column=0, sticky="w", pady=3)
        credits = tk.Frame(form, bg=PANEL)
        credits.grid(row=2, column=1, columnspan=3, sticky="w")
        self.credits_var = tk.StringVar()
        entry = ttk.Spinbox(credits, from_=0, to=9000, increment=50, textvariable=self.credits_var, width=8,
                            font=(FONT, 12, "bold"))
        entry.pack(side="left")
        button(credits, "Načítať z obrazovky (OCR)", self.read_credits_ocr, PANEL2).pack(side="left", padx=8)

        label(form, "Zostalo mi z kola", 10, MUTED, width=16, anchor="w").grid(row=3, column=0, sticky="w", pady=3)
        kept = tk.Frame(form, bg=PANEL)
        kept.grid(row=3, column=1, columnspan=3, sticky="w")
        self.kept_weapon_var = tk.StringVar(value="nič")
        self.kept_weapon_box = ttk.Combobox(kept, textvariable=self.kept_weapon_var, state="readonly", width=12,
                                            values=["nič"] + sorted(U.WEAPON_VALUE, key=lambda w: -U.WEAPON_VALUE[w]))
        self.kept_weapon_box.pack(side="left")
        self.kept_shield_var = tk.StringVar(value="Bez štítu")
        ttk.Combobox(kept, textvariable=self.kept_shield_var, state="readonly", width=14,
                     values=[v[0] for v in U.SHIELDS.values()]).pack(side="left", padx=6)
        label(kept, "(ak si prežil)", 8, MUTED).pack(side="left")

        label(form, "Plán tímu", 10, MUTED, width=16, anchor="w").grid(row=4, column=0, sticky="w", pady=3)
        self.plan_var = tk.StringVar(value="Neviem")
        ttk.Combobox(form, textvariable=self.plan_var, values=U.TEAM_PLANS, state="readonly", width=16).grid(
            row=4, column=1, sticky="w")

        actions = tk.Frame(body, bg=PANEL)
        actions.pack(fill="x", pady=(8, 6))
        button(actions, "Odporučiť nákup  ⏎", self.recommend_buy).pack(side="left")
        button(actions, "Ukončiť zápas", self.end_match_dialog, PANEL2).pack(side="right")
        button(actions, "Nový zápas", self.new_match, PANEL2).pack(side="right", padx=8)

        # Odporúčanie #
        self.buy_frame = tk.Frame(body, bg=PANEL2, highlightthickness=1, highlightbackground=LINE)
        self.buy_frame.pack(fill="x", pady=4)

        # Kolá tohto zápasu #
        columns = ("n", "tier", "buy", "credits", "kda", "result")
        self.rounds_tree = ttk.Treeview(body, columns=columns, show="headings", height=6)
        for col, text, width in zip(columns, ("Kolo", "Typ", "Nákup", "Kredity", "K/D/A v kole", "Výsledok"),
                                    (50, 110, 260, 70, 100, 80)):
            self.rounds_tree.heading(col, text=text)
            self.rounds_tree.column(col, width=width, anchor="w")
        self.rounds_tree.pack(fill="both", expand=True, pady=(6, 0))

    def update_agent_lists(self):
        roles = self.icons.roles()
        names = [""] + sorted(roles)
        for combo in self.mate_boxes:
            combo["values"] = names

    def refresh_mate_icons(self):
        roles = self.icons.roles()
        for var, (icon, role_label) in zip(self.mate_vars, self.mate_icons):
            name = var.get()
            photo = self.icons.photo("agent", name, 28) if name else None
            icon.configure(image=photo or "", width=28 if photo else 4)
            icon.image = photo
            role_label.configure(text=U.ROLE_SK.get(roles.get(name), "") if name else "")

    # Výber agenta #

    def recommend_agent(self):
        self.refresh_mate_icons()
        mates = [v.get() for v in self.mate_vars]
        result = L.recommend_agent(mates, self.map_var.get(), self.profile, self.icons.roles())
        self.agent_result = result
        for child in self.agent_cards.winfo_children():
            child.destroy()
        for i, agent in enumerate(U.MY_AGENTS):
            best = agent == result["choice"]
            box = tk.Frame(self.agent_cards, bg=PANEL2, highlightthickness=2,
                           highlightbackground=RED if best else LINE)
            box.grid(row=0, column=i, sticky="nsew", padx=(0, 8) if i == 0 else 0)
            self.agent_cards.columnconfigure(i, weight=1, uniform="a")
            head = tk.Frame(box, bg=PANEL2)
            head.pack(fill="x", padx=10, pady=8)
            photo = self.icons.photo("agent", agent, 48)
            if photo:
                img = tk.Label(head, image=photo, bg=PANEL2)
                img.image = photo
                img.pack(side="left", padx=(0, 8))
            texts = tk.Frame(head, bg=PANEL2)
            texts.pack(side="left")
            label(texts, agent.upper(), 14, RED if best else TEXT, True, bg=PANEL2).pack(anchor="w")
            label(texts, ("ODPORÚČANÉ – " + result["confidence"]) if best else f"skóre {result['scores'][agent]:.1f}",
                  9, GOLD if best else MUTED, bg=PANEL2).pack(anchor="w")
            for sign, text in result["reasons"][agent]:
                label(box, f"{sign} {text}", 9, GREEN if sign == "+" else RED, bg=PANEL2, wraplength=200).pack(
                    anchor="w", padx=10, pady=1)
            tk.Frame(box, bg=PANEL2, height=8).pack()
        self.agent_notes.configure(text="\n".join(result["notes"]))
        if not self.match or not self.match.get("agent"):
            self.overlay.show({"mode": "agent", "agent": result["choice"], "confidence": result["confidence"],
                               "reasons": [t for s, t in result["reasons"][result["choice"]] if s == "+"]})

    # Zápas #

    def start_match(self, agent):
        if self.match and self.match.get("rounds"):
            if not messagebox.askyesno("Rozohraný zápas", "Máš rozohraný zápas. Zahodiť ho a začať nový?"):
                return
        self.match = {
            "id": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "map": self.map_var.get(),
            "teammates": [v.get() for v in self.mate_vars if v.get()],
            "agent": agent,
            "recommended_agent": self.agent_result["choice"] if self.agent_result else None,
            "rounds": [],
            "score": [0, 0],
            "loss_streak": 0,
            "kda": [0, 0, 0],
            "result": None,
        }
        self.buy = None
        for var in self.kda_vars:
            var.set(0)
        S.save_current(self.match)
        self.refresh_match()
        self.recommend_buy()

    def new_match(self):
        if self.match and self.match.get("rounds"):
            answer = messagebox.askyesnocancel("Nový zápas", "Uložiť rozohraný zápas do histórie pred začatím nového?")
            if answer is None:
                return
            if answer:
                self.end_match_dialog()
                return
        self.match = None
        self.buy = None
        S.save_current(None)
        self.refresh_match()
        self.recommend_agent()

    def round_no(self):
        return len(self.match["rounds"]) + 1

    def pending_result(self):
        """Je predchádzajúce kolo ešte bez výsledku?"""
        return bool(self.match and self.match["rounds"] and self.match["rounds"][-1].get("won") is None)

    def tentative(self):
        """Skóre a séria prehier, ak by platil práve zvolený výsledok minulého kola."""
        us, them = self.match["score"]
        streak = self.match["loss_streak"]
        if self.pending_result() and self.result_var.get():
            if self.result_var.get() == "win":
                us, streak = us + 1, 0
            else:
                them, streak = them + 1, streak + 1
        if self.round_no() == 13:
            streak = 0  # po polčase sa séria prehier nuluje
        return us, them, streak

    def refresh_match(self):
        if not self.match or not self.match.get("agent"):
            self.round_header.configure(text="Najprv vyber agenta vľavo")
            self.round_sub.configure(text="Vyplň spoluhráčov, ktorých poznáš, a klikni Hrám Reynu / Hrám Breacha.")
            self.result_row.grid_remove()
            self.credits_var.set("")
            self.show_buy(None)
            self.fill_rounds_tree()
            return
        n = self.round_no()
        us, them = self.match["score"]
        self.round_header.configure(text=f"{self.match['agent'].upper()}  •  KOLO {n}  •  {us} : {them}")
        half = "1. polčas" if n <= 12 else "2. polčas" if n <= 24 else "overtime"
        self.round_sub.configure(text=f"{half}  •  mapa {self.match['map']}  •  séria prehier {self.match['loss_streak']}")
        if n > 1:
            self.result_row.grid()
        else:
            self.result_row.grid_remove()
        self.result_var.set("")
        default = L.default_credits(n)
        self.credits_var.set(str(default) if default is not None else "")
        if n in (1, 13, 25):
            self.kept_weapon_var.set("nič")
            self.kept_shield_var.set("Bez štítu")
        self.fill_rounds_tree()

    def fill_rounds_tree(self):
        self.rounds_tree.delete(*self.rounds_tree.get_children())
        if not self.match:
            return
        for r in self.match["rounds"]:
            kda = "" if r.get("kills") is None else f"{r['kills']}/{r['deaths']}/{r['assists']}"
            result = {True: "výhra", False: "prehra", None: "…"}[r.get("won")]
            buy = " + ".join([r["weapon"], U.SHIELDS[r["shield"]][0]] + r.get("abilities", []))
            self.rounds_tree.insert("", "end", values=(r["n"], r["tier"], buy, r["credits"], kda, result))

    def read_state(self):
        try:
            credits = int(float(self.credits_var.get()))
        except ValueError:
            messagebox.showwarning("Kredity", "Zadaj, koľko máš kreditov.")
            return None
        if self.pending_result() and not self.result_var.get():
            messagebox.showwarning("Minulé kolo", "Označ, či ste minulé kolo vyhrali alebo prehrali.")
            return None
        us, them, streak = self.tentative()
        kept = self.kept_weapon_var.get()
        shield = next((k for k, v in U.SHIELDS.items() if v[0] == self.kept_shield_var.get()), "none")
        return L.RoundState(agent=self.match["agent"], round_no=self.round_no(), credits=credits, loss_streak=streak,
                            score_us=us, score_them=them, kept_weapon=None if kept == "nič" else kept,
                            kept_shield=shield, team_plan=self.plan_var.get())

    def recommend_buy(self):
        if not self.match or not self.match.get("agent"):
            return
        if not self.credits_var.get():
            self.show_buy(None, "Zadaj kredity a stlač Enter.")
            return
        state = self.read_state()
        if not state:
            return
        if L.match_over(state.score_us, state.score_them):
            self.show_buy(None, "Zápas skončil – klikni na Ukončiť zápas.")
            return
        self.state = state
        self.buy = L.recommend_buy(state, self.profile, self.prices)
        self.show_buy(self.buy)

    def show_buy(self, buy, message=None):
        for child in self.buy_frame.winfo_children():
            child.destroy()
        if not buy:
            label(self.buy_frame, message or "Odporúčanie sa zobrazí tu.", 10, MUTED, bg=PANEL2).pack(padx=12, pady=16)
            if self.match and self.match.get("agent"):
                self.overlay.show({"mode": "waiting", "text": f"Kolo {self.round_no()} – zadaj kredity"})
            return
        colors = {"Full buy": GREEN, "Overtime": GREEN, "Force buy": RED, "All-in": RED, "Eco": MUTED}
        head = tk.Frame(self.buy_frame, bg=PANEL2)
        head.pack(fill="x", padx=12, pady=(10, 4))
        label(head, buy.tier.upper(), 16, colors.get(buy.tier, GOLD), True, bg=PANEL2).pack(side="left")
        label(head, f"Spolu {buy.cost}   •   zostane {buy.credits_left}", 11, TEXT, True, bg=PANEL2).pack(side="right")

        items = tk.Frame(self.buy_frame, bg=PANEL2)
        items.pack(fill="x", padx=12, pady=4)
        weapon_cost = 0 if buy.weapon == self.state.kept_weapon else self.prices["weapons"].get(buy.weapon, (0, ""))[0]
        self.item(items, self.icons.photo("weapon", buy.weapon, 46, max_width=170), buy.weapon, weapon_cost)
        if buy.shield != "none":
            cost = 0 if buy.shield == self.state.kept_shield else self.prices["shields"].get(buy.shield, 0)
            self.item(items, self.icons.photo("shield", buy.shield, 42), U.SHIELDS[buy.shield][0], cost)
        for slot, name, count, cost in L.group_abilities(buy.abilities):
            times = f" ×{count}" if count > 1 else ""
            self.item(items, self.icons.photo("ability", self.match["agent"], 38, slot=slot),
                      f"{name}{times} ({U.SLOT_KEY.get(slot, '?')})", cost)

        label(self.buy_frame, f"Ak kolo prehráte, budeš mať {buy.next_if_loss}.  Ak vyhráte, {buy.next_if_win}.",
              9, MUTED, bg=PANEL2).pack(anchor="w", padx=12)
        for reason in buy.reasons:
            label(self.buy_frame, "• " + reason, 9, TEXT, bg=PANEL2, wraplength=620).pack(anchor="w", padx=12)
        if buy.tip:
            label(self.buy_frame, "Tip: " + buy.tip, 9, GOLD, bg=PANEL2, wraplength=620).pack(anchor="w", padx=12, pady=(2, 0))

        confirm = tk.Frame(self.buy_frame, bg=PANEL2)
        confirm.pack(fill="x", padx=12, pady=10)
        button(confirm, "✔ Kúpil som to", lambda: self.confirm_buy(buy.weapon, buy.shield), GREEN, BG).pack(side="left")
        label(confirm, "  alebo som kúpil:", 9, MUTED, bg=PANEL2).pack(side="left")
        other_weapon = tk.StringVar(value=buy.weapon)
        ttk.Combobox(confirm, textvariable=other_weapon, state="readonly", width=10,
                     values=sorted(U.WEAPON_VALUE, key=lambda w: -U.WEAPON_VALUE[w])).pack(side="left", padx=4)
        other_shield = tk.StringVar(value=U.SHIELDS[buy.shield][0])
        ttk.Combobox(confirm, textvariable=other_shield, state="readonly", width=13,
                     values=[v[0] for v in U.SHIELDS.values()]).pack(side="left", padx=4)
        button(confirm, "Uložiť", lambda: self.confirm_buy(
            other_weapon.get(), next(k for k, v in U.SHIELDS.items() if v[0] == other_shield.get())),
            PANEL, TEXT).pack(side="left", padx=4)

        us, them, _ = self.tentative()
        self.overlay.show({"mode": "buy", "round": self.round_no(), "score": f"{us}:{them}", "tier": buy.tier,
                           "agent": self.match["agent"], "weapon": buy.weapon, "shield": buy.shield,
                           "shield_name": U.SHIELDS[buy.shield][0].replace(" Shields", "").replace(" Shield", ""),
                           "abilities": L.group_abilities(buy.abilities), "cost": buy.cost, "credits_left": buy.credits_left,
                           "next_if_loss": buy.next_if_loss, "next_if_win": buy.next_if_win, "tip": buy.tip})

    def item(self, parent, photo, name, cost):
        box = tk.Frame(parent, bg=PANEL, padx=8, pady=6)
        box.pack(side="left", padx=(0, 8))
        if photo:
            img = tk.Label(box, image=photo, bg=PANEL, height=50)
            img.image = photo
            img.pack()
        label(box, name, 9, TEXT, True).pack()
        label(box, "zadarmo" if cost == 0 else str(cost), 8, GOLD if cost else MUTED).pack()

    def commit_previous_result(self):
        """Zapíše výsledok a K/D/A minulého kola."""
        if not self.pending_result():
            return
        prev = self.match["rounds"][-1]
        won = self.result_var.get() == "win"
        prev["won"] = won
        kda = [v.get() for v in self.kda_vars]
        start = prev.get("kda_start", [0, 0, 0])
        prev["kills"], prev["deaths"], prev["assists"] = [max(0, a - b) for a, b in zip(kda, start)]
        self.match["kda"] = kda
        if won:
            self.match["score"][0] += 1
            self.match["loss_streak"] = 0
        else:
            self.match["score"][1] += 1
            self.match["loss_streak"] += 1

    def confirm_buy(self, weapon, shield):
        if not self.buy:
            return
        self.commit_previous_result()
        us, them = self.match["score"]
        if L.match_over(us, them):
            self.end_match_dialog()
            return
        if self.round_no() == 13:
            self.match["loss_streak"] = 0
        abilities = [name for _, name, _ in self.buy.abilities]
        self.match["rounds"].append({
            "n": self.round_no(), "credits": self.state.credits, "tier": self.buy.tier,
            "weapon": weapon, "shield": shield, "abilities": abilities, "cost": self.buy.cost,
            "recommended": {"weapon": self.buy.weapon, "shield": self.buy.shield},
            "kda_start": [v.get() for v in self.kda_vars], "won": None,
            "kills": None, "deaths": None, "assists": None,
        })
        S.save_current(self.match)
        self.buy = None
        self.refresh_match()
        self.show_buy(None, f"Kolo {self.round_no() - 1} uložené. Po kole zadaj výsledok, K/D/A a nové kredity.")

    # Koniec zápasu #

    def end_match_dialog(self):
        if not self.match or not self.match.get("agent"):
            return
        win = tk.Toplevel(self.root, bg=PANEL)
        win.title("Koniec zápasu")
        win.transient(self.root)
        win.grab_set()
        body = tk.Frame(win, bg=PANEL)
        body.pack(padx=20, pady=16)
        label(body, "KONIEC ZÁPASU", 14, RED, True).pack(anchor="w")
        last_var = tk.StringVar(value=self.result_var.get() or "")
        if self.pending_result():
            label(body, "Posledné kolo:", 10, MUTED).pack(anchor="w", pady=(10, 0))
            row = tk.Frame(body, bg=PANEL)
            row.pack(anchor="w")
            ttk.Radiobutton(row, text="Vyhrali sme", value="win", variable=last_var).pack(side="left")
            ttk.Radiobutton(row, text="Prehrali sme", value="loss", variable=last_var).pack(side="left", padx=10)
        label(body, "Konečné K / D / A:", 10, MUTED).pack(anchor="w", pady=(10, 0))
        row = tk.Frame(body, bg=PANEL)
        row.pack(anchor="w")
        final = [tk.IntVar(value=v.get()) for v in self.kda_vars]
        for var in final:
            ttk.Spinbox(row, from_=0, to=99, textvariable=var, width=4).pack(side="left", padx=(0, 6))
        label(body, "Výsledok zápasu:", 10, MUTED).pack(anchor="w", pady=(10, 0))
        us, them = self.match["score"]
        result_var = tk.StringVar(value="win" if us > them else "loss" if them > us else "")
        row = tk.Frame(body, bg=PANEL)
        row.pack(anchor="w")
        for value, text in (("win", "Výhra"), ("loss", "Prehra"), ("draw", "Remíza / surrender")):
            ttk.Radiobutton(row, text=text, value=value, variable=result_var).pack(side="left", padx=(0, 10))

        def save():
            if self.pending_result():
                if not last_var.get():
                    messagebox.showwarning("Posledné kolo", "Označ výsledok posledného kola.", parent=win)
                    return
                self.result_var.set(last_var.get())
                for var, value in zip(self.kda_vars, final):
                    var.set(value.get())
                self.commit_previous_result()
            self.match["kda"] = [v.get() for v in final]
            us, them = self.match["score"]
            result = result_var.get() or ("win" if us > them else "loss" if them > us else "draw")
            self.match["result"] = result
            self.history.append(self.match)
            S.save_history(self.history)
            S.save_current(None)
            self.profile = L.Profile(self.history)
            self.match = None
            self.buy = None
            win.destroy()
            self.refresh_match()
            self.recommend_agent()
            self.fill_history()
            messagebox.showinfo("Uložené", "Zápas je uložený v histórii. Program sa z neho naučil nové veci.")

        buttons = tk.Frame(body, bg=PANEL)
        buttons.pack(fill="x", pady=(14, 0))
        button(buttons, "Uložiť zápas", save).pack(side="left")
        button(buttons, "Zrušiť", win.destroy, PANEL2).pack(side="left", padx=8)

    # # # ZÁLOŽKA: HISTÓRIA # # #

    def build_history_tab(self):
        t = self.tab_history
        frame, body = card(t, "Odohrané zápasy")
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        columns = ("date", "map", "agent", "rec", "score", "result", "kda", "kd", "rounds")
        self.history_tree = ttk.Treeview(body, columns=columns, show="headings", height=12)
        for col, text, width in zip(columns, ("Dátum", "Mapa", "Agent", "Odporúčaný", "Skóre", "Výsledok", "K/D/A",
                                              "K/D", "Kôl"), (140, 90, 80, 90, 70, 80, 90, 60, 50)):
            self.history_tree.heading(col, text=text)
            self.history_tree.column(col, width=width, anchor="w")
        self.history_tree.pack(fill="both", expand=True)
        self.history_tree.bind("<<TreeviewSelect>>", lambda e: self.show_history_rounds())
        row = tk.Frame(body, bg=PANEL)
        row.pack(fill="x", pady=6)
        button(row, "Zmazať vybraný zápas", self.delete_match, PANEL2).pack(side="left")
        self.history_info = label(row, "", 9, MUTED)
        self.history_info.pack(side="left", padx=12)
        columns = ("n", "tier", "buy", "rec", "credits", "kda", "result")
        self.history_rounds = ttk.Treeview(body, columns=columns, show="headings", height=8)
        for col, text, width in zip(columns, ("Kolo", "Typ", "Kúpil som", "Odporúčané", "Kredity", "K/D/A", "Výsledok"),
                                    (50, 110, 220, 150, 70, 70, 70)):
            self.history_rounds.heading(col, text=text)
            self.history_rounds.column(col, width=width, anchor="w")
        self.history_rounds.pack(fill="both", expand=True)
        self.fill_history()

    def fill_history(self):
        self.history_tree.delete(*self.history_tree.get_children())
        for i, m in reversed(list(enumerate(self.history))):
            k, d, a = m.get("kda", [0, 0, 0])
            result = {"win": "VÝHRA", "loss": "prehra", "draw": "remíza"}.get(m.get("result"), "?")
            self.history_tree.insert("", "end", iid=str(i), values=(
                m["date"], m.get("map", ""), m["agent"], m.get("recommended_agent") or "",
                f"{m['score'][0]}:{m['score'][1]}", result, f"{k}/{d}/{a}", f"{k / max(1, d):.2f}", len(m["rounds"])))
        self.history_info.configure(text=f"Spolu {len(self.history)} zápasov")

    def show_history_rounds(self):
        self.history_rounds.delete(*self.history_rounds.get_children())
        selection = self.history_tree.selection()
        if not selection:
            return
        match = self.history[int(selection[0])]
        for r in match["rounds"]:
            kda = "" if r.get("kills") is None else f"{r['kills']}/{r['deaths']}/{r['assists']}"
            rec = r.get("recommended", {})
            same = rec.get("weapon") == r["weapon"]
            self.history_rounds.insert("", "end", values=(
                r["n"], r["tier"], " + ".join([r["weapon"], U.SHIELDS[r["shield"]][0]] + r.get("abilities", [])),
                ("✔ " if same else "") + str(rec.get("weapon", "")), r["credits"], kda,
                {True: "výhra", False: "prehra", None: "?"}[r.get("won")]))

    def delete_match(self):
        selection = self.history_tree.selection()
        if selection and messagebox.askyesno("Zmazať", "Naozaj zmazať vybraný zápas?"):
            del self.history[int(selection[0])]
            S.save_history(self.history)
            self.profile = L.Profile(self.history)
            self.fill_history()
            self.history_rounds.delete(*self.history_rounds.get_children())

    # # # ZÁLOŽKA: ANALÝZA # # #

    def build_analysis_tab(self):
        t = self.tab_analysis
        frame, self.learned = card(t, "Čo sa program o tebe naučil")
        frame.pack(side="bottom", fill="x", padx=12, pady=(0, 10))
        self.tiles = tk.Frame(t, bg=BG)
        self.tiles.pack(fill="x", padx=8, pady=(8, 0))
        grid = tk.Frame(t, bg=BG)
        grid.pack(fill="both", expand=True, padx=8, pady=8)
        for c in range(2):
            grid.columnconfigure(c, weight=1, uniform="g")
        for r in range(2):
            grid.rowconfigure(r, weight=1, uniform="g")
        self.charts = []
        for i in range(4):
            canvas = tk.Canvas(grid, bg=PANEL, highlightthickness=1, highlightbackground=LINE)
            canvas.grid(row=i // 2, column=i % 2, sticky="nsew", padx=4, pady=4)
            canvas.bind("<Configure>", lambda e: self.draw_charts())
            self.charts.append(canvas)

    def refresh_analysis(self):
        for child in self.tiles.winfo_children():
            child.destroy()
        games = [m for m in self.history if m.get("result") in ("win", "loss")]
        wins = sum(m["result"] == "win" for m in games)
        kills = sum(m.get("kda", [0, 0, 0])[0] for m in self.history)
        deaths = sum(m.get("kda", [0, 0, 0])[1] for m in self.history)
        rounds = sum(len(m["rounds"]) for m in self.history)
        tiles = [("Zápasy", str(len(self.history))),
                 ("Winrate", f"{round(100 * wins / len(games))} %" if games else "–"),
                 ("K/D", f"{kills / max(1, deaths):.2f}" if self.history else "–"),
                 ("Killy / kolo", f"{kills / rounds:.2f}" if rounds else "–")]
        for name, value in tiles:
            box = tk.Frame(self.tiles, bg=PANEL, highlightthickness=1, highlightbackground=LINE)
            box.pack(side="left", fill="x", expand=True, padx=4)
            label(box, name.upper(), 9, MUTED, True).pack(anchor="w", padx=12, pady=(8, 0))
            label(box, value, 22, TEXT, True).pack(anchor="w", padx=12, pady=(0, 8))
        self.draw_charts()

        for child in self.learned.winfo_children():
            child.destroy()
        for line in self.learned_lines():
            label(self.learned, "• " + line, 10, TEXT, wraplength=1100).pack(anchor="w")

    def draw_charts(self):
        if not self.charts:
            return
        p = self.profile
        agents = []
        for agent in U.MY_AGENTS:
            a = p.agents.get(agent)
            if a and a["games"]:
                agents.append((agent, 100 * a["wins"] / a["games"], f"{a['games']} záp."))
        grafy.draw_bars(self.charts[0], "Winrate podľa agenta", agents, RED, max_value=100)

        order = ["Pistolové kolo", "Eco", "Bonus kolo", "Half buy", "Force buy", "All-in", "Full buy", "Overtime"]
        tiers = [(t, 100 * p.tiers[t]["wins"] / p.tiers[t]["rounds"], f"{p.tiers[t]['rounds']} kôl")
                 for t in order if t in p.tiers and p.tiers[t]["rounds"]]
        grafy.draw_bars(self.charts[1], "Vyhraté kolá podľa typu nákupu", tiers, RED, max_value=100)

        weapons = sorted(p.weapons.items(), key=lambda kv: -kv[1]["rounds"])[:7]
        items = [(w, s["kills"] / s["rounds"], f"{s['rounds']} kôl") for w, s in weapons if s["rounds"]]
        grafy.draw_bars(self.charts[2], "Killy za kolo podľa zbrane", items, RED, fmt="{:.2f}")

        kds = []
        for m in self.history[-15:]:
            k, d, _ = m.get("kda", [0, 0, 0])
            kds.append(k / max(1, d))
        grafy.draw_line(self.charts[3], "K/D v posledných zápasoch (čiarkovane 1.0)", kds, RED, reference=1.0)

    def learned_lines(self):
        p = self.profile
        if not self.history:
            return ["Zatiaľ žiadne zápasy. Po každom uloženom zápase sa odporúčania prispôsobia tvojej hre."]
        lines = []
        for agent in U.MY_AGENTS:
            winrate, kd, games = p.agent_stats(agent)
            if games:
                lines.append(f"{agent}: {games} zápasov, odhad winrate {round(winrate * 100)} %, K/D {kd:.2f}.")
        v, ph = p.weapon_factor("Vandal"), p.weapon_factor("Phantom")
        if abs(v - ph) > 0.03:
            lines.append(f"Lepšie ti ide {'Vandal' if v > ph else 'Phantom'} – pri full buy ho program uprednostní.")
        sheriff, ghost = p.weapon_factor("Sheriff"), p.weapon_factor("Ghost")
        if abs(sheriff - ghost) > 0.03:
            lines.append(f"Na eco ti viac sedí {'Sheriff' if sheriff > ghost else 'Ghost'}.")
        force_wr, force_n = p.tier_winrate("Force buy", 0.33)
        if force_n:
            advice = "program ti ich bude viac odporúčať" if force_wr >= 0.45 else "radšej šetri"
            lines.append(f"Force buye: odhad {round(force_wr * 100)} % výhier ({force_n} kôl) – {advice}.")
        pistol_wr, pistol_n = p.tier_winrate("Pistolové kolo", 0.5)
        if pistol_n:
            lines.append(f"Pistolové kolá: {round(pistol_wr * 100)} % výhier ({pistol_n}).")
        followed = [r for m in self.history for r in m["rounds"] if r.get("won") is not None and r.get("recommended")]
        same = [r for r in followed if r["recommended"].get("weapon") == r["weapon"]]
        other = [r for r in followed if r["recommended"].get("weapon") != r["weapon"]]
        if len(same) >= 5 and len(other) >= 5:
            a = 100 * sum(r["won"] for r in same) / len(same)
            b = 100 * sum(r["won"] for r in other) / len(other)
            lines.append(f"Keď si kúpil odporúčanú zbraň, vyhrali ste {a:.0f} % kôl, inak {b:.0f} %.")
        lines.append(f"Priemerne máš {p.kills_per_round:.2f} killu za kolo – podľa toho program váži presné zbrane (Sheriff, Marshal, Guardian).")
        return lines

    # # # ZÁLOŽKA: NASTAVENIA # # #

    def build_settings_tab(self):
        t = self.tab_settings
        frame, body = card(t, "Overlay a monitory")
        frame.pack(fill="x", padx=8, pady=8)
        label(body, "Overlay presúvaš ťahaním myšou, veľkosť meníš rohom vpravo dole, pravé tlačidlo = menu.\n"
                    "Aby bol overlay nad hrou, nastav vo Valorante Video → Display Mode: Windowed Fullscreen.",
              9, MUTED).pack(anchor="w")
        row = tk.Frame(body, bg=PANEL)
        row.pack(fill="x", pady=8)
        label(row, "Priehľadnosť", 10, MUTED, width=14, anchor="w").pack(side="left")
        self.alpha_var = tk.DoubleVar(value=self.settings["overlay_alpha"])
        ttk.Scale(row, from_=0.3, to=1.0, variable=self.alpha_var, length=220,
                  command=lambda v: self.set_alpha(float(v))).pack(side="left")
        label(row, "Veľkosť písma", 10, MUTED, width=14, anchor="w").pack(side="left", padx=(20, 0))
        self.scale_var = tk.DoubleVar(value=self.settings["overlay_scale"])
        ttk.Scale(row, from_=0.6, to=2.0, variable=self.scale_var, length=220,
                  command=lambda v: self.set_scale(float(v))).pack(side="left")
        row = tk.Frame(body, bg=PANEL)
        row.pack(fill="x")
        button(row, "Hlavné okno na ľavý monitor", self.place_main_left, PANEL2).pack(side="left")
        button(row, "Overlay na pravý monitor", self.place_overlay_right, PANEL2).pack(side="left", padx=8)

        frame, body = card(t, "OCR – automatické čítanie kreditov (experimentálne)")
        frame.pack(fill="x", padx=8, pady=8)
        label(body, "Program si odfotí malý výrez obrazovky, kde hra ukazuje kredity, a prečíta číslo. Do hry nezasahuje.\n"
                    "Treba: pip install mss pytesseract  +  program Tesseract OCR (odkaz v README).", 9, MUTED).pack(anchor="w")
        row = tk.Frame(body, bg=PANEL)
        row.pack(fill="x", pady=6)
        label(row, "Tesseract", 10, MUTED, width=14, anchor="w").pack(side="left")
        self.tess_var = tk.StringVar(value=self.settings["tesseract_cmd"])
        ttk.Entry(row, textvariable=self.tess_var, width=60).pack(side="left")
        button(row, "Nájsť…", self.browse_tesseract, PANEL2).pack(side="left", padx=6)
        row = tk.Frame(body, bg=PANEL)
        row.pack(fill="x", pady=4)
        button(row, "Vybrať oblasť s kreditmi", self.select_region, PANEL2).pack(side="left")
        button(row, "Otestovať", self.test_ocr, PANEL2).pack(side="left", padx=8)
        self.ocr_auto_var = tk.BooleanVar(value=self.settings["ocr_auto"])
        ttk.Checkbutton(row, text="Čítať automaticky každé 2 s", variable=self.ocr_auto_var,
                        command=lambda: self.toggle_ocr_auto(self.ocr_auto_var.get())).pack(side="left", padx=12)
        self.ocr_status = label(body, "", 9, GOLD)
        self.ocr_status.pack(anchor="w")
        self.update_ocr_status()

        frame, body = card(t, "Údaje")
        frame.pack(fill="x", padx=8, pady=8)
        label(body, f"História a nastavenia sú v priečinku: {S.FOLDER}", 9, MUTED).pack(anchor="w")
        label(body, "Ceny schopností (Reyna, Breach) sú v súbore udaje.py – ak ich Riot zmení, uprav ich tam.", 9,
              MUTED).pack(anchor="w")
        row = tk.Frame(body, bg=PANEL)
        row.pack(fill="x", pady=6)
        button(row, "Otvoriť priečinok s dátami", self.open_data_folder, PANEL2).pack(side="left")

    def set_alpha(self, value):
        self.settings["overlay_alpha"] = round(value, 2)
        self.overlay.attributes("-alpha", value)
        self.save_settings()

    def set_scale(self, value):
        self.settings["overlay_scale"] = round(value, 1)
        self.overlay.render()
        self.save_settings()

    def place_main_left(self):
        x, y, _, _ = virtual_screen(self.root)
        self.root.geometry(f"+{x + 30}+{y + 30}")

    def place_overlay_right(self):
        x, y, w, _ = virtual_screen(self.root)
        self.overlay.update_idletasks()
        width = self.overlay.winfo_width() if self.overlay.winfo_width() > 1 else 400
        self.overlay.geometry(f"+{x + w - width - 30}+{y + 60}")
        self.settings["overlay_geometry"] = self.overlay.geometry()
        self.save_settings()

    def toggle_overlay(self):
        if self.settings["overlay_visible"]:
            self.overlay.hide()
        else:
            self.overlay.show_window()

    # OCR #

    def update_ocr_status(self):
        ok, text = ocr.available(self.tess_var.get())
        region = self.settings["ocr_region"]
        where = f"Oblasť: {region}" if region else "Oblasť ešte nie je vybraná."
        self.ocr_status.configure(text=f"{text}  {where}", fg=GREEN if ok and region else GOLD)
        return ok

    def browse_tesseract(self):
        path = filedialog.askopenfilename(title="tesseract.exe", filetypes=[("Tesseract", "tesseract*"), ("Všetko", "*")])
        if path:
            self.tess_var.set(path)
            self.settings["tesseract_cmd"] = path
            self.save_settings()
            self.update_ocr_status()

    def select_region(self):
        """Priehľadná plocha cez všetky monitory – myšou označ obdĺžnik s kreditmi."""
        x, y, w, h = virtual_screen(self.root)
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.geometry(f"{w}x{h}+{x}+{y}")
        win.attributes("-topmost", True)
        win.attributes("-alpha", 0.35)
        canvas = tk.Canvas(win, bg="black", highlightthickness=0, cursor="crosshair")
        canvas.pack(fill="both", expand=True)
        canvas.create_text(w / 2, 40, text="Potiahni myšou obdĺžnik okolo čísla kreditov (Esc = zrušiť)",
                           fill="white", font=(FONT, 18, "bold"))
        start = {}

        def press(e):
            start["x"], start["y"] = e.x_root, e.y_root
            start["rect"] = canvas.create_rectangle(e.x, e.y, e.x, e.y, outline=RED, width=3)

        def drag(e):
            canvas.coords(start["rect"], start["x"] - x, start["y"] - y, e.x, e.y)

        def release(e):
            left, top = min(start["x"], e.x_root), min(start["y"], e.y_root)
            width, height = abs(e.x_root - start["x"]), abs(e.y_root - start["y"])
            win.destroy()
            if width > 5 and height > 5:
                self.settings["ocr_region"] = [left, top, width, height]
                self.save_settings()
                self.update_ocr_status()
                self.test_ocr()

        canvas.bind("<ButtonPress-1>", press)
        canvas.bind("<B1-Motion>", drag)
        canvas.bind("<ButtonRelease-1>", release)
        win.bind("<Escape>", lambda e: win.destroy())
        win.focus_force()

    def ocr_value(self):
        self.settings["tesseract_cmd"] = self.tess_var.get()
        if not self.settings["ocr_region"] or not ocr.available(self.tess_var.get())[0]:
            return None
        try:
            return ocr.read_credits(self.settings["ocr_region"])
        except Exception:
            return None

    def test_ocr(self):
        if not self.update_ocr_status():
            return
        value = self.ocr_value()
        self.ocr_status.configure(text=f"Prečítané: {value}" if value is not None else
                                  "Nepodarilo sa prečítať číslo – skús oblasť vybrať tesnejšie okolo čísla.")

    def read_credits_ocr(self):
        value = self.ocr_value()
        if value is None:
            messagebox.showinfo("OCR", "OCR nie je nastavené alebo nič neprečítalo. Pozri záložku Nastavenia.")
            return
        self.credits_var.set(str(value))
        self.recommend_buy()

    def toggle_ocr_auto(self, on):
        self.settings["ocr_auto"] = on
        self.save_settings()
        if self.ocr_job:
            self.root.after_cancel(self.ocr_job)
            self.ocr_job = None
        if on:
            self.ocr_tick()

    def ocr_tick(self):
        value = self.ocr_value()
        if value is not None and self.match and self.match.get("agent") and str(value) != self.credits_var.get():
            self.credits_var.set(str(value))
            if not self.pending_result() or self.result_var.get():
                self.recommend_buy()
        self.ocr_job = self.root.after(2000, self.ocr_tick)

    def open_data_folder(self):
        os.makedirs(S.FOLDER, exist_ok=True)
        try:
            os.startfile(S.FOLDER)
        except AttributeError:
            messagebox.showinfo("Priečinok", S.FOLDER)

    # # # OSTATNÉ # # #

    def refresh_tab(self):
        tab = self.tabs.index(self.tabs.select())
        if tab == 1:
            self.fill_history()
        elif tab == 2:
            self.refresh_analysis()

    def poll_icons(self):
        """Keď na pozadí dobehne sťahovanie z API, prekreslí okná s ikonami a novými cenami."""
        if self.icons.version != self.icon_version:
            self.icon_version = self.icons.version
            if self.icons.ready:
                self.icons.update_prices(self.prices)
                self.update_agent_lists()
            self.recommend_agent()
            if self.buy:
                self.show_buy(self.buy)
            else:
                self.overlay.render()
        self.api_label.configure(text=self.icons.status)
        self.root.after(1000, self.poll_icons)

    def save_settings(self):
        S.save_settings(self.settings)

    def quit(self):
        self.settings["main_geometry"] = self.root.geometry()
        self.settings["overlay_geometry"] = self.overlay.geometry()
        self.save_settings()
        self.root.destroy()

    def run(self):
        self.recommend_agent()
        if self.match and self.match.get("agent"):
            self.refresh_match()
            self.recommend_buy()
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
