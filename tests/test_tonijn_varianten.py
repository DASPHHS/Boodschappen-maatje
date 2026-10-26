"""Controleer brede tonijnopties, correcte ingrediënten en veilige bronmatching."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from tonijn_varianten import TUNA_RECIPES,TUNA_METHODS
from receptenradar_catalog import ING,RECIPES,RECIPE_METHODS,validate_dish_ingredients
from receptkwaliteit import cooking_instructions,dish_quality_issues,pantry_for_recipe
from recept_keukens import infer_cuisine
from receptenradar_v2 import match_ingredient

class TonijnVariantenTests(unittest.TestCase):
    def test_brede_unieke_gerechten(self):
        titles=[r[0] for r in TUNA_RECIPES]
        self.assertGreaterEqual(len(titles),25)
        self.assertEqual(len(titles),len(set(titles)))
        self.assertEqual(len(titles),len(set(titles)&{r[0] for r in RECIPES}))
        self.assertGreaterEqual(sum(t.startswith("Lunch:") for t in titles),4)
        self.assertGreaterEqual(len({infer_cuisine(t) for t in titles}),10)
    def test_ingrediënten_en_gerechtvormen(self):
        for title,category,minutes,ingredients in TUNA_RECIPES:
            with self.subTest(title=title):
                self.assertEqual(category,"Vis")
                self.assertTrue(10<=minutes<=45)
                keys=[k for k,_,_ in ingredients]
                self.assertIn("tonijn",keys)
                self.assertEqual(len(keys),len(set(keys)))
                self.assertTrue(all(k in ING and qty>0 and unit in ("g","st","ml") for k,qty,unit in ingredients))
                self.assertEqual(validate_dish_ingredients(title,ingredients),[])
                self.assertEqual(dish_quality_issues(title,category,ingredients),[])
                self.assertIn(title,RECIPE_METHODS)
    def test_uitvoerbare_bereidingen(self):
        for title,category,minutes,ingredients in TUNA_RECIPES:
            with self.subTest(title=title):
                method=cooking_instructions(title,ingredients,TUNA_METHODS[title])
                self.assertGreater(len(method),150)
                self.assertIn("tonijn",method.lower())
                self.assertTrue("uitlekken" in method.lower() or "uit blik af" in method.lower())
                self.assertTrue(pantry_for_recipe(title,ingredients,method))
    def test_productmatching_alleen_echte_tonijn(self):
        good=["AH Tonijnstukken in water","Jumbo Tonijnstukken in olie","John West Tonijn in eigen nat","Tonijnfilets in olijfolie","Tonijn uit blik naturel"]
        bad=["John West Twist Diner Tonijn Mexicaans","Pizza tonijn","Tonijnsalade als broodbeleg","Tonijnsteak vers","Tonijn pasta maaltijd"]
        for name in good:
            with self.subTest(good=name):
                self.assertTrue(match_ingredient({"norm":name.casefold()},"tonijn"))
        for name in bad:
            with self.subTest(bad=name):
                self.assertFalse(match_ingredient({"norm":name.casefold()},"tonijn"))

if __name__=="__main__":unittest.main()
