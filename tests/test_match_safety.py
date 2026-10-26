"""Regressions for offer-driven recipe ingredient matching."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from meal_planner import matches

class MatchSafetyTests(unittest.TestCase):
    def test_matching(self):
        cases = [
            ("Kipdrumsticks 1 kg", "kipfilet", False),
            ("Hele kip 1,2 kg", "kipfilet", False),
            ("Kipfilet 500 g", "kipfilet", True),
            ("Kippenbouillon", "kip", False),
            ("Rijstwafels naturel", "rijst", False),
            ("Zilvervliesrijst 1 kg", "rijst", True),
            ("Eierkoeken 6 stuks", "ei", False),
        ]
        for title, ingredient, expected in cases:
            with self.subTest(title=title, ingredient=ingredient):
                self.assertEqual(matches(title, ingredient), expected)

if __name__ == "__main__":
    unittest.main()
