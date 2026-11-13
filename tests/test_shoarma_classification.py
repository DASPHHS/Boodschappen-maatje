"""Regression tests for promotion ingredient classification."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync_aanbiedingen.py"
spec = importlib.util.spec_from_file_location("sync_aanbiedingen", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ShoarmaClassificationTests(unittest.TestCase):
    def test_meat_and_chicken(self):
        for name, expected in [
            ("Jumbo Shoarma", "vlees"),
            ("Varkensshoarma", "vlees"),
            ("Shoarmavlees", "vlees"),
            ("Kipshoarma", "kip"),
            ("Kip shoarma", "kip"),
            ("Vegetarische shoarma", "vega"),
            ("Vegan shoarma", "vega"),
        ]:
            with self.subTest(name=name):
                self.assertEqual(module.kind(name), expected)

    def test_excludes_sauces_and_seasonings(self):
        for name in ("Shoarmakruiden", "Shoarmasaus", "Kipshoarma kruidenmix"):
            with self.subTest(name=name):
                self.assertIsNone(module.kind(name))

if __name__ == "__main__":
    unittest.main()
