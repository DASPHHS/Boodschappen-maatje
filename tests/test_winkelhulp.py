import json
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from build_winkelhulp import build, option, price_line, active_offer, matches, ROOT


class ShoppingView(unittest.TestCase):
    def test_real_catalog_has_ten_per_category_and_traced_sources(self):
        catalog = json.loads((ROOT / "winkelhulp/recipes.json").read_text())
        self.assertEqual(len(catalog["recipes"]), 40)
        for category in ("kip", "vlees", "vis", "vega"):
            self.assertEqual(sum(r["category"] == category for r in catalog["recipes"]), 10)
        for recipe in catalog["recipes"]:
            self.assertEqual(recipe["servings"], 4)
            self.assertTrue(recipe["source"]["file_id"])
            self.assertTrue(recipe["source"]["title"])
            self.assertTrue(recipe["adaptation"])
        self.assertTrue(any("Surinaamse" in r["source"]["file_name"] for r in catalog["recipes"]))
        self.assertTrue(any(f["status"] == "not_processed" for f in catalog["source_files"]))

    def test_no_piece_weight_assumption_or_shrinking(self):
        ing = {"key": "kip", "quantity": 800, "unit": "g", "label": "kipfilet"}
        row = ["Kipfilet", 5, 750, "g", "https://example.com"]
        result = option(ing, row)
        self.assertEqual(result["packages"], 2)
        self.assertEqual(result["checkout"], 10)
        self.assertEqual(result["leftover"], 700)
        self.assertIsNone(option({"key": "paprikavers", "quantity": 600, "unit": "g"},
                                 ["Paprika", 1, 1, "st", "https://example.com"]))

    def test_exact_bundle_and_dates(self):
        ing = {"key": "broccoli", "quantity": 1200, "unit": "g"}
        row = ["Broccoli", 2, 500, "g", 2, 2, 2, "multi_buy", "2026-10-27", "https://example.com", True, "2026-10-21"]
        self.assertTrue(active_offer(row, date(2026, 10, 27)))
        self.assertFalse(active_offer(row, date(2026, 10, 28)))
        result = option(ing, row, True)
        self.assertEqual(result["checkout"], 4)
        self.assertTrue(result["loyalty"])
        self.assertIsNone(price_line(ing, {"promotions": [row]}, date(2026, 10, 28))["price"])

    def test_unknown_drained_and_skin_states_are_not_confirmed(self):
        self.assertFalse(matches("tonijn", "Tonijnstukken in water"))
        self.assertFalse(matches("gehakt", "Half om half gehakt"))
        self.assertFalse(matches("kip", "Kipfilet broodbeleg"))
        self.assertFalse(matches("garnalen", "Ongepelde garnalen"))
        self.assertFalse(matches("zalm", "Zalmfilet met huid"))
        p = option({"key": "zalm", "quantity": 800, "unit": "g"},
                   ["Zalmfilet", 8, 400, "g", "https://example.com"])
        self.assertFalse(p["form_verified"])

    def test_prepared_food_and_flavours_are_not_raw_ingredients(self):
        unsafe = [("kip", "Jumbo Scharrel Kipfilet Gerookt 120g"),
                  ("knoflook", "AH Bakaardappeltjes paprika en knoflook"),
                  ("paprikavers", "Duyvis Tijgernootjes BBQ Paprika"),
                  ("broccoli", "Knorr Good Potatoes Kaas Broccoli"),
                  ("broccoli", "AH Bloemkool broccoli kleinverpakking"),
                  ("courgette", "Jumbo Stamppotje Wortel Courgette 6m"),
                  ("gember", "Klene Puur gember"),
                  ("gember", "Hero v-spread gember"),
                  ("italiaans", "Grillworst met Italiaanse kruiden kaas"),
                  ("raselhanout", "Maza Hoemoes ras el hanout"),
                  ("biefstuk", "Biefstuk tapenade olijf parmezaan"),
                  ("spitskool", "Slaverrijker spitskool wortel")]
        for key, name in unsafe:
            with self.subTest(key=key, name=name):
                self.assertFalse(matches(key, name))
        self.assertTrue(matches("kip", "Jumbo Scharrel Kipfilet 800 g"))
        self.assertTrue(matches("broccoli", "AH Broccoliroosjes"))

    def test_missing_cost_is_not_a_full_price(self):
        recipe = {"id": "test", "title": "Kip", "category": "kip", "ingredients": [
            {"key": "kip", "quantity": 800, "unit": "g", "label": "kipfilet"},
            {"key": "unknown", "quantity": 200, "unit": "g", "label": "iets"}]}
        result = build({"recipes": [recipe], "source_files": [], "coverage_note": "test"},
                       {"stores": {"ah": {"ordinary": [["Kipfilet", 8, 800, "g", "https://example.com"]]}}}, date(2026, 10, 27))
        r = result["stores"]["ah"][0]
        self.assertFalse(r["complete"])
        self.assertEqual(r["known_used"], 8)
        self.assertIsNone(r["per_serving"])


if __name__ == "__main__":
    unittest.main()
