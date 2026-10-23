"""Regressietests voor kassaprijzen en voorzichtige productmatching."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from receptenradar_v2 import measure,match_ingredient,total_for,promo_for,ingredient_price,nutrition_profile

class PrijsTest(unittest.TestCase):
    def test_dertig_gram_eiwit_per_portie(self):
        # 650g kipfilet + 800g broccoli voor vier porties.
        high=nutrition_profile([("kipfilet",650,"g"),("broccoli",800,"g")])
        self.assertGreaterEqual(high["protein_g_per_serving_estimate"],30)
        self.assertTrue(high["protein_source"])
        low=nutrition_profile([("tofu",450,"g"),("broccoli",600,"g")])
        self.assertLess(low["protein_g_per_serving_estimate"],30)
        self.assertFalse(low["protein_source"])

    def test_verpakkingen(self):
        self.assertEqual(measure("2 x 125 g"),(250,"g"))
        self.assertEqual(measure("0,75 liter"),(750,"ml"))
        self.assertEqual(measure("per stuk"),(1,"st"))
        self.assertEqual(measure("500 g"),(500,"g"))

    def test_bundel_kassa(self):
        promo={"price":2,"original_price":4,"multi_buy_quantity":2,"multi_buy_price":4}
        self.assertEqual(total_for(2,4,promo),(4,2))
        self.assertEqual(total_for(3,4,promo),(8,3))

    def test_blijf_weg_bij_verkeerde_ingrediënten(self):
        self.assertFalse(match_ingredient({"norm":"kipfilet plantaardig 200 g"},"kipfilet"))
        self.assertFalse(match_ingredient({"norm":"witte bonen tomatensaus"},"tomaten"))
        self.assertFalse(match_ingredient({"norm":"zoete aardappelgratin 400 g"},"zoete_aardappel"))
        self.assertFalse(match_ingredient({"norm":"jumbo spinazie a la creme 800 g"},"spinazie"))
        self.assertFalse(match_ingredient({"norm":"no fairytales paprika wraps"},"paprika"))
        self.assertFalse(match_ingredient({"norm":"gedroogde linzen 500 g"},"linzen"))
        self.assertTrue(match_ingredient({"norm":"ah kipfilet 600 g"},"kipfilet"))

    def test_geen_bonus_op_onjuist_artikel(self):
        shelf={"norm":"ah tomatenblokjes 400 g","unit":"g","quantity":400,"price":.69}
        offer={"norm":"ah cherrytomaten 400 g","unit":"g","quantity":400,"original_price":.69,"price":.35}
        self.assertIsNone(promo_for(shelf,[offer]))

    def test_onbekende_schapprijs_niet_geschat(self):
        self.assertIsNone(ingredient_price("kipfilet",600,"g",[],[]))

    def test_meerdere_verpakkingen(self):
        p={"norm":"ah kipfilet 400 g","name":"AH Kipfilet 400 g","quantity":400,
           "unit":"g","price":4.0,"size_label":"400 g","url":"https://ah.nl/"}
        r=ingredient_price("kipfilet",600,"g",[p],[])
        self.assertEqual(r["packages"],2)
        self.assertEqual(r["cash_price"],8)
        self.assertEqual(r["used_price"],6)
if __name__=="__main__":unittest.main()
