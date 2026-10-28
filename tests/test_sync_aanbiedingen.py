import unittest
from scripts.sync_aanbiedingen import category, kind, item

class PromotionCoverageTest(unittest.TestCase):
    def test_all_shopping_categories(self):
        examples = {
            "Grolsch Herfstbok 6x300ML": "bier",
            "Hertog Jan Pils 6 x 300 ml": "bier",
            "Leffe Blond": "bier",
            "Heineken 0.0 Bier": "bier",
            "Dreft Platinum Plus 25 stuks": "huishouden",
            "Calvé Pindakaas 350 g": "voorraad",
            "Zespri SunGold Kiwi": "fruit",
            "Campina magere kwark": "zuivel",
            "Jumbo prei": "groente",
            "AH Terra Plantaardige Kipstukjes": "vega",
            "Knorr Kipkruiden": "overig",
        }
        for name, expected in examples.items():
            with self.subTest(name=name):
                self.assertEqual(category(name), expected)

    def test_recipe_matching_remains_strict(self):
        self.assertIsNone(kind("Knorr Kipkruiden"))
        self.assertIsNone(kind("Grolsch Herfstbok 6 x 300ml"))
        self.assertEqual(kind("AH Terra Plantaardige Kipstukjes"), "vega")

    def test_full_feed_keeps_non_recipe_products(self):
        p = dict(product_id="beer_1", name="Grolsch Herfstbok Bier",
            promotion_status="active", valid_from="2026-10-26",
            valid_until="2026-11-03", price=6.18, original_price=8.25)
        product=item(p, "2026-10-28")
        self.assertIsNotNone(product)
        self.assertEqual(product["category"], "bier")
        self.assertFalse(product["recipe_ingredient_candidate"])
        self.assertIsNone(item(p, "2026-11-04"))

if __name__ == "__main__":
    unittest.main()
