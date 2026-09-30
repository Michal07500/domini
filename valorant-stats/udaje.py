"""Statické údaje o Valorante.

Ceny zbraní a štítov sa pri spustení aktualizujú z valorant-api.com (ak je internet).
Ceny schopností API neposkytuje – ak Riot niečo zmení, uprav ich tu v ABILITIES.
"""

# Role agentov (nový agent, ktorý tu chýba, sa doplní automaticky z API) #
ROLES = {
    "Astra": "Controller", "Brimstone": "Controller", "Clove": "Controller", "Harbor": "Controller",
    "Omen": "Controller", "Viper": "Controller",
    "Iso": "Duelist", "Jett": "Duelist", "Neon": "Duelist", "Phoenix": "Duelist", "Raze": "Duelist",
    "Reyna": "Duelist", "Waylay": "Duelist", "Yoru": "Duelist",
    "Breach": "Initiator", "Fade": "Initiator", "Gekko": "Initiator", "KAY/O": "Initiator",
    "Skye": "Initiator", "Sova": "Initiator", "Tejo": "Initiator",
    "Chamber": "Sentinel", "Cypher": "Sentinel", "Deadlock": "Sentinel", "Killjoy": "Sentinel",
    "Sage": "Sentinel", "Veto": "Sentinel", "Vyse": "Sentinel",
}

ROLE_SK = {"Duelist": "duelista", "Initiator": "initiator", "Controller": "controller", "Sentinel": "sentinel"}

# Agenti, na ktorých sa hráč púšťa a pre ktorých program radí nákup schopností #
MY_AGENTS = ["Reyna", "Breach"]

# Duelisti, ktorým Breach výborne pripravuje vstup (stun/flash pred entry) #
BREACH_SYNERGY = {"Raze", "Jett", "Neon", "Iso", "Phoenix", "Yoru", "Waylay"}

# Schopnosti: slot -> (názov, cena, max. nábojov, priorita nákupu – nižšie = dôležitejšie) #
# Slot podľa valorant-api.com: Grenade = C, Ability1 = Q, Ability2 = E, Ultimate = X #
ABILITIES = {
    "Reyna": [
        ("Grenade", "Leer", 250, 1, 1),
        ("Ability1", "Devour", 100, 2, 2),
        ("Grenade", "Leer", 250, 1, 3),   # druhý náboj Leer
        ("Ability2", "Dismiss", 100, 2, 4),
    ],
    "Breach": [
        ("Ability1", "Flashpoint", 250, 1, 1),
        ("Grenade", "Aftershock", 200, 1, 2),
        ("Ability1", "Flashpoint", 250, 1, 3),  # druhý náboj Flashpoint
    ],
}
SLOT_KEY = {"Grenade": "C", "Ability1": "Q", "Ability2": "E", "Ultimate": "X"}

# Záložné ceny (prepíšu sa cenami z API) a kategória zbrane #
WEAPONS = {
    "Classic": (0, "Sidearm"), "Shorty": (300, "Sidearm"), "Frenzy": (450, "Sidearm"),
    "Ghost": (500, "Sidearm"), "Bandit": (600, "Sidearm"), "Sheriff": (800, "Sidearm"),
    "Stinger": (1100, "SMG"), "Spectre": (1600, "SMG"),
    "Bucky": (850, "Shotgun"), "Judge": (1850, "Shotgun"),
    "Bulldog": (2050, "Rifle"), "Guardian": (2250, "Rifle"), "Phantom": (2900, "Rifle"), "Vandal": (2900, "Rifle"),
    "Marshal": (950, "Sniper"), "Outlaw": (2400, "Sniper"), "Operator": (4700, "Sniper"),
    "Ares": (1600, "Heavy"), "Odin": (3200, "Heavy"),
}

# Základná "sila" zbrane v kole (0–1). Program ju upravuje podľa tvojich výsledkov #
WEAPON_VALUE = {
    "Vandal": 1.00, "Phantom": 1.00, "Operator": 0.95, "Guardian": 0.80, "Outlaw": 0.80, "Bulldog": 0.78,
    "Judge": 0.66, "Spectre": 0.70, "Odin": 0.68, "Ares": 0.58, "Marshal": 0.60, "Stinger": 0.55,
    "Bucky": 0.50, "Sheriff": 0.50, "Bandit": 0.46, "Ghost": 0.42, "Frenzy": 0.38, "Shorty": 0.30,
    "Classic": 0.28,
}
PRECISION_WEAPONS = {"Sheriff", "Marshal", "Guardian", "Outlaw", "Operator", "Vandal"}

# Štíty: kľúč -> (názov, cena, hodnota) #
SHIELDS = {
    "none": ("Bez štítu", 0, 0.0),
    "light": ("Light Shields", 400, 0.25),
    "regen": ("Regen Shield", 650, 0.32),
    "heavy": ("Heavy Shields", 1000, 0.45),
}

# Ekonomika #
PISTOL_CREDITS = 800
OT_CREDITS = 5000
MAX_CREDITS = 9000
WIN_REWARD = 3000
LOSS_BONUS = [1900, 2400, 2900]
KILL_REWARD = 200
PLANT_REWARD = 300
ROUNDS_TO_WIN = 13
HALF_ROUNDS = 12

# Mapy: (bonus pre Reynu, bonus pre Breacha) – hrubý odhad, dá sa upraviť #
MAPS = {
    "Neviem": (0.0, 0.0),
    "Abyss": (0.3, -0.2), "Ascent": (0.0, 0.3), "Bind": (0.0, 0.4), "Breeze": (0.3, -0.3),
    "Corrode": (0.1, 0.1), "Fracture": (-0.1, 0.6), "Haven": (0.0, 0.3), "Icebox": (0.2, -0.2),
    "Lotus": (0.0, 0.4), "Pearl": (0.2, 0.0), "Split": (0.0, 0.4), "Sunset": (0.1, 0.2),
}

TEAM_PLANS = ["Neviem", "Full buy", "Force buy", "Eco / šetríme"]
