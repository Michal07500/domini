"""Logika odporúčaní – výber agenta, nákup na každé kolo a učenie sa z histórie.

Všetko je obyčajný Python bez okien, takže sa to dá ľahko testovať (test_logika.py).
"""

from dataclasses import dataclass, field
from itertools import product

import udaje as U


def smooth(wins, n, prior, k):
    """Bayesovský priemer: pri málo dátach verí predpokladu, pri veľa dátach tvojim výsledkom."""
    return (wins + prior * k) / (n + k)


# # # PROFIL HRÁČA – čo sa program naučil z histórie # # #

class Profile:
    def __init__(self, matches):
        self.agents = {}   # agent -> {"games", "wins", "kills", "deaths", "rounds"}
        self.weapons = {}  # zbraň -> {"rounds", "wins", "kills"}
        self.tiers = {}    # typ nákupu -> {"rounds", "wins"}
        self.rounds = 0
        self.kills = 0
        for match in matches:
            self.add_match(match)

    def add_match(self, match):
        agent = match.get("agent")
        a = self.agents.setdefault(agent, {"games": 0, "wins": 0, "kills": 0, "deaths": 0, "rounds": 0})
        if match.get("result") in ("win", "loss"):
            a["games"] += 1
            a["wins"] += match["result"] == "win"
        for r in match.get("rounds", []):
            if r.get("won") is None:
                continue
            kills, deaths = r.get("kills") or 0, r.get("deaths") or 0
            a["kills"] += kills
            a["deaths"] += deaths
            a["rounds"] += 1
            self.rounds += 1
            self.kills += kills
            w = self.weapons.setdefault(r.get("weapon") or "Classic", {"rounds": 0, "wins": 0, "kills": 0})
            w["rounds"] += 1
            w["wins"] += bool(r["won"])
            w["kills"] += kills
            t = self.tiers.setdefault(r.get("tier") or "?", {"rounds": 0, "wins": 0})
            t["rounds"] += 1
            t["wins"] += bool(r["won"])

    # Hodnoty #

    @property
    def kills_per_round(self):
        return smooth(self.kills, self.rounds, 0.7, 20)

    def agent_stats(self, agent):
        a = self.agents.get(agent, {"games": 0, "wins": 0, "kills": 0, "deaths": 0, "rounds": 0})
        winrate = smooth(a["wins"], a["games"], 0.5, 5)
        kd = (a["kills"] + 5) / (a["deaths"] + 5)
        return winrate, kd, a["games"]

    def weapon_factor(self, weapon):
        """Násobok sily zbrane podľa toho, ako ti s ňou ide (1.0 = bez dát)."""
        w = self.weapons.get(weapon, {"rounds": 0, "wins": 0, "kills": 0})
        winrate = smooth(w["wins"], w["rounds"], 0.45, 8)
        kpr = smooth(w["kills"], w["rounds"], 0.7, 8)
        factor = 1 + 0.6 * (winrate - 0.45) + 0.3 * (kpr - 0.7)
        if weapon in U.PRECISION_WEAPONS:
            factor += 0.15 * (self.kills_per_round - 0.7)
        return max(0.6, min(1.5, factor))

    def weapon_note(self, weapon):
        w = self.weapons.get(weapon)
        if not w or w["rounds"] < 3:
            return None
        return (f"{weapon}: {round(100 * w['wins'] / w['rounds'])} % vyhratých kôl, "
                f"{w['kills'] / w['rounds']:.2f} killu/kolo ({w['rounds']} kôl)")

    def tier_winrate(self, tier, prior):
        t = self.tiers.get(tier, {"rounds": 0, "wins": 0})
        return smooth(t["wins"], t["rounds"], prior, 8), t["rounds"]


# # # VÝBER AGENTA: REYNA ALEBO BREACH # # #

def recommend_agent(teammates, map_name, profile, roles=None):
    roles = roles or U.ROLES
    known = [t for t in teammates if t]
    count = {"Duelist": 0, "Initiator": 0, "Controller": 0, "Sentinel": 0}
    for agent in known:
        role = roles.get(agent)
        if role in count:
            count[role] += 1

    scores = {"Reyna": 0.0, "Breach": 0.0}
    reasons = {"Reyna": [], "Breach": []}
    notes = []

    def add(agent, value, text):
        scores[agent] += value
        reasons[agent].append(("+" if value >= 0 else "−", text))

    duel, init = count["Duelist"], count["Initiator"]
    if duel == 0:
        add("Reyna", 2.0, "Tím nemá duelistu – niekto musí ísť prvý (entry).")
    elif duel == 1:
        add("Breach", 0.8, "Duelistu už máte – Breach mu stunom a flashom otvorí vstup.")
    else:
        add("Reyna", -1.5, f"V tíme sú už {duel} duelisti.")
        add("Breach", 1.2, "Viac duelistov potrebuje niekoho s utilitou.")

    if init == 0:
        add("Breach", 1.5, "Chýba initiator – bez flashov a stunov sa ťažko vstupuje na site.")
    elif init >= 2:
        add("Breach", -1.0, f"Initiatorov je už {init}.")
        add("Reyna", 0.5, "Info a flashe tím má, chýba skôr fragovanie.")

    partners = sorted(BREACH_PARTNERS & set(known))
    if partners:
        add("Breach", 0.4, "Dobrá synergia s: " + ", ".join(partners) + ".")

    if count["Controller"] == 0 and len(known) >= 3:
        notes.append("Pozor: v tíme zatiaľ nie je controller (smoky).")
    if count["Sentinel"] == 0 and len(known) >= 3:
        notes.append("V tíme nie je sentinel – na obrane stráž flanky.")

    reyna_map, breach_map = U.MAPS.get(map_name or "Neviem", (0.0, 0.0))
    if reyna_map:
        add("Reyna", reyna_map, f"Mapa {map_name} {'sedí' if reyna_map > 0 else 'nesedí'} Reyne.")
    if breach_map:
        add("Breach", breach_map, f"Mapa {map_name} {'sedí' if breach_map > 0 else 'nesedí'} Breachovi.")

    # Tvoje osobné výsledky – čím viac zápasov, tým väčšia váha #
    for agent in scores:
        winrate, kd, games = profile.agent_stats(agent)
        if games:
            weight = games / (games + 5)
            value = weight * ((winrate - 0.5) * 4 + (kd - 1) * 1.5)
            add(agent, value, f"Tvoje výsledky: {round(winrate * 100)} % výhier, K/D {kd:.2f} ({games} zápasov).")

    if len(known) < 4:
        notes.append(f"Poznáš {len(known)} zo 4 spoluhráčov – odporúčanie sa ešte môže zmeniť.")

    choice = max(scores, key=scores.get)
    margin = abs(scores["Reyna"] - scores["Breach"])
    confidence = "jasne" if margin >= 1.5 else "skôr" if margin >= 0.5 else "tesne"
    return {"choice": choice, "scores": scores, "reasons": reasons, "notes": notes,
            "confidence": confidence, "roles": count}


BREACH_PARTNERS = U.BREACH_SYNERGY


# # # NÁKUP NA KOLO # # #

@dataclass
class RoundState:
    agent: str
    round_no: int
    credits: int
    loss_streak: int = 0
    score_us: int = 0
    score_them: int = 0
    kept_weapon: str = None       # zbraň, ktorá ti zostala z minulého kola
    kept_shield: str = "none"     # štít, ktorý ti zostal
    team_plan: str = "Neviem"


@dataclass
class Buy:
    tier: str
    weapon: str
    shield: str
    abilities: list = field(default_factory=list)  # [(slot, názov, cena)]
    cost: int = 0
    credits_left: int = 0
    next_if_loss: int = 0
    next_if_win: int = 0
    reasons: list = field(default_factory=list)
    tip: str = ""


def round_kind(state):
    n = state.round_no
    if n >= 25:
        return "overtime"
    if n in (1, 13):
        return "pistol"
    if n in (2, 14):
        return "second"
    if n in (12, 24):
        return "last_of_half"
    return "normal"


def loss_bonus(streak):
    return U.LOSS_BONUS[min(max(streak, 0), len(U.LOSS_BONUS) - 1)]


def ability_value(priority):
    return {1: 0.08, 2: 0.05, 3: 0.04}.get(priority, 0.03)


def best_loadout(state, budget, profile, prices, sidearms_only=False, force_heavy=False):
    """Vyskúša všetky kombinácie zbraň + štít + schopnosti a vyberie najlepšiu, ktorá sa zmestí do rozpočtu."""
    abilities = sorted(U.ABILITIES.get(state.agent, []), key=lambda a: a[4])
    ability_options = [abilities[:i] for i in range(len(abilities) + 1)]

    weapons = []
    for name, (cost, category) in prices["weapons"].items():
        if name not in U.WEAPON_VALUE:
            continue
        if sidearms_only and category != "Sidearm":
            continue
        weapons.append((name, 0 if name == state.kept_weapon else cost))
    if state.kept_weapon and all(w[0] != state.kept_weapon for w in weapons):
        weapons.append((state.kept_weapon, 0))
    if not any(w[0] == "Classic" for w in weapons):
        weapons.append(("Classic", 0))

    shield_rank = ["none", "light", "regen", "heavy"]
    best = None
    for (weapon, w_cost), shield, abil in product(weapons, U.SHIELDS, ability_options):
        s_name, s_cost, s_value = U.SHIELDS[shield]
        s_cost = prices["shields"].get(shield, s_cost)
        if state.kept_shield and state.kept_shield != "none":
            if shield_rank.index(shield) < shield_rank.index(state.kept_shield):
                continue  # horší štít, než máš, nemá zmysel
            if shield == state.kept_shield:
                s_cost = 0
        a_cost = sum(a[2] for a in abil)
        total = w_cost + s_cost + a_cost
        if total > budget:
            continue
        if force_heavy and shield != "heavy" and budget >= w_cost + prices["shields"].get("heavy", 1000):
            continue
        value = U.WEAPON_VALUE[weapon] * profile.weapon_factor(weapon) + s_value
        if state.kept_weapon and weapon != state.kept_weapon and w_cost > 0:
            if U.WEAPON_VALUE.get(state.kept_weapon, 0) >= 0.95:
                continue  # dobrú pušku z minulého kola nemá zmysel meniť
            value -= 0.12  # slabšiu zbraň vymeň len za výrazne lepšiu
        value += sum(ability_value(a[4]) for a in abil)
        value -= total * 0.000005  # pri rovnakej hodnote radšej lacnejšie
        if best is None or value > best[0]:
            best = (value, weapon, shield, abil, total)
    _, weapon, shield, abil, total = best
    return weapon, shield, [(a[0], a[1], a[2]) for a in abil], total


def recommend_buy(state, profile, prices):
    kind = round_kind(state)
    reasons = []
    credits = state.credits
    rifle_cost = prices["weapons"].get("Vandal", (2900, "Rifle"))[0]
    heavy_cost = prices["shields"].get("heavy", 1000)
    key_ability = min((a[2] for a in U.ABILITIES.get(state.agent, []) if a[4] == 1), default=0)
    if state.kept_weapon and U.WEAPON_VALUE.get(state.kept_weapon, 0) >= 0.95:
        rifle_cost = 0  # puška ti zostala z minulého kola
    if state.kept_shield == "heavy":
        heavy_cost = 0
    full_min = rifle_cost + heavy_cost + key_ability
    next_loss = loss_bonus(state.loss_streak)

    if kind == "pistol":
        tier, budget = "Pistolové kolo", credits
        reasons.append("Pistolové kolo – každý má 800 kreditov.")
        pistol_wr, n = profile.tier_winrate(tier, 0.5)
        if n >= 4:
            reasons.append(f"Tvoje pistolovky: {round(pistol_wr * 100)} % výhier ({n} kôl).")
        weapon, shield, abil, cost = best_loadout(state, budget, profile, prices, sidearms_only=True)
    elif kind == "overtime":
        tier = "Overtime"
        reasons.append("Overtime – každé kolo 5000 kreditov, kupuj naplno.")
        weapon, shield, abil, cost = best_loadout(state, credits, profile, prices)
    else:
        all_in = kind == "last_of_half" or (state.score_them == U.ROUNDS_TO_WIN - 1 and state.score_us < U.ROUNDS_TO_WIN - 1)
        max_spend = credits + next_loss - full_min  # toľko môžeš minúť a budúce kolo aj tak full buy
        force_wr, force_n = profile.tier_winrate("Force buy", 0.33)

        if credits >= full_min:
            tier, budget = "Full buy", credits
            reasons.append(f"Máš na plný nákup (treba ~{full_min}).")
        elif all_in:
            tier, budget = "All-in", credits
            if kind == "last_of_half":
                reasons.append("Posledné kolo polčasu – kredity sa potom vynulujú, míňaj všetko.")
            else:
                reasons.append("Súper má match point – nie je na čo šetriť.")
        elif state.team_plan == "Force buy":
            tier, budget = "Force buy", credits
            reasons.append("Tím ide force – kupuj s nimi, sám na eco nepomôžeš.")
        elif state.team_plan == "Eco / šetríme":
            tier, budget = "Eco", max(0, min(max_spend, 500))
            reasons.append("Tím šetrí – ber len lacné veci, nech je budúce kolo full buy.")
        elif kind == "second" and state.loss_streak == 0:
            tier, budget = "Bonus kolo", credits
            reasons.append("Vyhrali ste pistolovku – bonus kolo, kup SMG/lacnú pušku a štít.")
        elif max_spend >= 2000:
            tier, budget = "Half buy", max_spend
            reasons.append(f"Na full nemáš, ale môžeš minúť do {max_spend} a budúce kolo aj tak kúpiš naplno.")
        elif credits >= 2000 and force_n >= 5 and force_wr >= 0.45:
            tier, budget = "Force buy", credits
            reasons.append(f"Tvoje force buye vychádzajú ({round(force_wr * 100)} % výhier z {force_n}) – oplatí sa riskovať.")
        else:
            tier, budget = "Eco", max(0, min(max_spend, 1000))
            reasons.append(f"Šetri. Ak prehráte, budeš mať aspoň {credits - budget + next_loss} "
                           f"(full buy stojí ~{full_min}).")
        weapon, shield, abil, cost = best_loadout(state, budget, profile, prices,
                                                  force_heavy=tier in ("Full buy", "Overtime"))

    if state.kept_weapon and weapon == state.kept_weapon:
        reasons.append(f"Nechaj si {weapon} z minulého kola.")
    note = profile.weapon_note(weapon)
    if note:
        reasons.append(note)

    left = credits - cost
    buy = Buy(tier=tier, weapon=weapon, shield=shield, abilities=abil, cost=cost, credits_left=left,
              next_if_loss=min(U.MAX_CREDITS, left + next_loss), next_if_win=min(U.MAX_CREDITS, left + U.WIN_REWARD),
              reasons=reasons)
    buy.tip = make_tip(state.agent, buy, prices["weapons"].get("Vandal", (2900, ""))[0] + prices["shields"].get("heavy", 1000))
    return buy


def make_tip(agent, buy, full_cost):
    if buy.tier in ("Full buy", "Overtime") and buy.credits_left >= full_cost - 1000:
        return f"Zostane ti {buy.credits_left} – kúp zbraň spoluhráčovi, čo nemá."
    if agent == "Breach":
        if buy.tier == "Eco":
            return "Aj na eco sa oplatí Flashpoint – oslepí ich pri tvojom peeku."
        if buy.tier == "Pistolové kolo":
            return "Flashpoint cez stenu a hneď peek s tímom."
        return "Fault Line pred vstupom na site, Aftershock na rohy a spike."
    if agent == "Reyna":
        if buy.tier == "Eco":
            return "Hraj na jeden kill a zober zbraň – Devour ťa vylieči."
        if buy.tier == "Pistolové kolo":
            return "Leer hoď pred peekom, po kille Dismiss späť do bezpečia."
        return "Leer pred entry; po kille Devour (život) alebo Dismiss (únik)."
    return ""


# # # POMÔCKY PRE ZÁPAS # # #

def group_abilities(abilities):
    """[(slot, názov, cena), ...] -> [(slot, názov, počet, spolu), ...] – dva náboje ukáže ako ×2."""
    grouped = {}
    for slot, name, cost in abilities:
        if name in grouped:
            g = grouped[name]
            grouped[name] = (slot, name, g[2] + 1, g[3] + cost)
        else:
            grouped[name] = (slot, name, 1, cost)
    return list(grouped.values())


def match_over(us, them):
    if us < U.ROUNDS_TO_WIN and them < U.ROUNDS_TO_WIN:
        return False
    if us >= U.HALF_ROUNDS and them >= U.HALF_ROUNDS:
        return abs(us - them) >= 2
    return True


def default_credits(round_no):
    if round_no >= 25:
        return U.OT_CREDITS
    if round_no in (1, 13):
        return U.PISTOL_CREDITS
    return None


def default_prices():
    return {"weapons": dict(U.WEAPONS), "shields": {k: v[1] for k, v in U.SHIELDS.items()}}
