"""Testy logiky odporúčaní. Spustenie: python -m unittest test_logika.py"""

import unittest

import logika as L

PRICES = L.default_prices()
EMPTY = L.Profile([])


def buy(**kw):
    return L.recommend_buy(L.RoundState(**kw), EMPTY, PRICES)


def fake_round(n, weapon, won, kills, tier="Full buy"):
    return {"n": n, "tier": tier, "weapon": weapon, "shield": "heavy", "won": won, "kills": kills, "deaths": 1}


class BuyTests(unittest.TestCase):
    def test_pistol_round_stays_within_800(self):
        for agent in ("Reyna", "Breach"):
            b = buy(agent=agent, round_no=1, credits=800)
            self.assertEqual(b.tier, "Pistolové kolo")
            self.assertLessEqual(b.cost, 800)
            self.assertIn(b.weapon, ("Classic", "Ghost", "Sheriff", "Frenzy", "Shorty", "Bandit"))

    def test_eco_after_lost_pistol(self):
        b = buy(agent="Breach", round_no=2, credits=2100, loss_streak=1)
        self.assertEqual(b.tier, "Eco")
        self.assertGreaterEqual(b.next_if_loss, 3900)  # budúce kolo musí byť full buy

    def test_full_buy(self):
        b = buy(agent="Reyna", round_no=6, credits=5000)
        self.assertEqual(b.tier, "Full buy")
        self.assertIn(b.weapon, ("Vandal", "Phantom"))
        self.assertEqual(b.shield, "heavy")

    def test_keeps_weapon_from_last_round(self):
        b = buy(agent="Breach", round_no=7, credits=2600, kept_weapon="Phantom", kept_shield="light")
        self.assertEqual(b.weapon, "Phantom")
        self.assertEqual(b.tier, "Full buy")
        self.assertLessEqual(b.cost, 1700)

    def test_last_round_of_half_spends_everything(self):
        b = buy(agent="Breach", round_no=12, credits=2200, loss_streak=1)
        self.assertEqual(b.tier, "All-in")
        self.assertGreater(b.cost, 1500)

    def test_overtime(self):
        self.assertEqual(buy(agent="Reyna", round_no=25, credits=5000).tier, "Overtime")

    def test_never_overspends(self):
        for credits in range(0, 9001, 150):
            for n in (3, 5, 12, 20):
                b = buy(agent="Reyna", round_no=n, credits=credits, loss_streak=n % 4)
                self.assertLessEqual(b.cost, credits)


class LearningTests(unittest.TestCase):
    def test_prefers_rifle_that_works_for_player(self):
        rounds = [fake_round(i, "Phantom", True, 2) for i in range(30)]
        rounds += [fake_round(i, "Vandal", False, 0) for i in range(30)]
        profile = L.Profile([{"agent": "Reyna", "result": "win", "rounds": rounds}])
        b = L.recommend_buy(L.RoundState(agent="Reyna", round_no=6, credits=5000), profile, PRICES)
        self.assertEqual(b.weapon, "Phantom")

    def test_agent_choice_uses_team(self):
        no_duelist = L.recommend_agent(["Omen", "Killjoy", "Sova"], "Neviem", EMPTY)
        self.assertEqual(no_duelist["choice"], "Reyna")
        two_duelists = L.recommend_agent(["Jett", "Raze", "Omen"], "Neviem", EMPTY)
        self.assertEqual(two_duelists["choice"], "Breach")


class MatchTests(unittest.TestCase):
    def test_match_over(self):
        self.assertTrue(L.match_over(13, 7))
        self.assertFalse(L.match_over(12, 12))
        self.assertFalse(L.match_over(13, 12))
        self.assertTrue(L.match_over(14, 12))

    def test_group_abilities(self):
        grouped = L.group_abilities([("Ability1", "Flashpoint", 250), ("Grenade", "Aftershock", 200),
                                     ("Ability1", "Flashpoint", 250)])
        self.assertEqual(grouped[0], ("Ability1", "Flashpoint", 2, 500))


if __name__ == "__main__":
    unittest.main()
