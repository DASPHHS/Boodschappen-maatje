"""Regressietests voor kassaprijzen en voorzichtige productmatching."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from receptenradar_v2 import measure,match_ingredient,total_for,promo_for,ingredient_price,nutrition_profile,product_context,audit_promotions,alternative_offers

class PrijsTest(unittest.TestCase):
    def test_kcal_per_portie_en_totaal(self):
        recipe=nutrition_profile([
            ("kipfilet",800,"g"),("broccoli",1000,"g"),
            ("aardappel",400,"g")])
        # 880 kcal kip + 340 kcal broccoli + 320 kcal aardappelen.
        self.assertEqual(recipe["kcal_total_estimate"],1540)
        self.assertEqual(recipe["kcal_per_serving_estimate"],385)
        self.assertEqual(recipe["kcal_unknown"],[])

    def test_geen_schijnzekerheid_bij_ontbrekende_voedingswaarde(self):
        recipe=nutrition_profile([("kipfilet",800,"g"),("onbekend",100,"g")])
        self.assertIsNone(recipe["kcal_per_serving_estimate"])
        self.assertIn("onbekend",recipe["kcal_unknown"])

    def test_dertig_gram_eiwit_per_portie(self):
        # 650g kipfilet + 800g broccoli voor vier porties.
        high=nutrition_profile([("kipfilet",650,"g"),("broccoli",800,"g")])
        self.assertGreaterEqual(high["protein_g_per_serving_estimate"],30)
        self.assertTrue(high["protein_source"])
        low=nutrition_profile([("tofu",450,"g"),("broccoli",600,"g")])
        self.assertLess(low["protein_g_per_serving_estimate"],30)
        self.assertFalse(low["protein_source"])

    def test_meer_groenten_in_plaats_van_zetmeel(self):
        sufficient=nutrition_profile([("kipfilet",650,"g"),
            ("spruiten",1100,"g"),("aardappel",400,"g")])
        self.assertEqual(sufficient["vegetable_g_per_serving_estimate"],275)
        self.assertTrue(sufficient["lower_carb"])
        self.assertTrue(sufficient["priority"])
        insufficient=nutrition_profile([("kipfilet",650,"g"),
            ("spruiten",800,"g"),("aardappel",900,"g")])
        self.assertFalse(insufficient["vegetable_forward"])
        self.assertFalse(insufficient["lower_carb"])

    def test_ontbijt_zonder_groente_toch_passend(self):
        p=nutrition_profile([
          ("kwark",1400,"g"),("havermout",160,"g"),
          ("banaan",480,"g"),("blauwe_bessen",300,"g")],meal_type="Ontbijt")
        self.assertTrue(p["priority"])
        self.assertTrue(p["protein_source"])
        self.assertGreater(p["kcal_per_serving_estimate"],300)

    def test_lunch_met_groenten(self):
        p=nutrition_profile([("kipfilet",800,"g"),("broccoli",800,"g"),
                             ("wortel",300,"g"),("rijst",140,"g")],meal_type="Lunch")
        self.assertTrue(p["priority"])
        self.assertGreaterEqual(p["protein_g_per_serving_estimate"],30)

    def test_jumbo_magere_milde_kwark_herkend(self):
        self.assertTrue(match_ingredient(
            {"norm":"campina magere milde kwark naturel voordeelpak 1 kg"},"kwark"))
        self.assertTrue(match_ingredient(
            {"norm":"jumbo nederlandse aardbeien 400 g"},"aardbeien"))
        self.assertFalse(match_ingredient(
            {"norm":"optimel kwark met yoghurt aardbei 500 g"},"kwark"))

    def test_vaste_aanbieding_voor_prijs(self):
        promo={"price":2.49,"original_price":3.49,
               "promotion_type":"voor € 2,49"}
        self.assertEqual(total_for(2,3.49,promo),(4.98,2))
        unverified_bundle={"price":2.99,"original_price":3.49,
                           "promotion_type":"2 voor 2,99"}
        self.assertEqual(total_for(2,3.49,unverified_bundle),(6.98,2))

    def test_gezonde_varianten_en_diepvries(self):
        self.assertTrue(match_ingredient(
            {"norm":"optimel magere kwark vanille zonder toegevoegde suiker 500 g"},"kwark"))
        self.assertTrue(match_ingredient(
            {"norm":"skyr aardbei 450 g"},"kwark"))
        self.assertTrue(match_ingredient(
            {"norm":"diepvries blauwe bessen 750 g"},"blauwe_bessen"))
        self.assertTrue(match_ingredient(
            {"norm":"diepvries broccoli roosjes 1000 g"},"broccoli"))
        self.assertTrue(match_ingredient(
            {"norm":"diepvries zalmfilet 500 g"},"zalm"))
        self.assertFalse(match_ingredient(
            {"norm":"aardbeien kwark dessert mousse"},"kwark"))
        self.assertFalse(match_ingredient(
            {"norm":"blauwe bessen jam"},"blauwe_bessen"))
        ctx=product_context({"name":"Diepvries blauwe bessen 750 g"},"blauwe_bessen")
        self.assertTrue(ctx["frozen"])
        flav=product_context({"name":"Skyr aardbei 450 g"},"kwark")
        self.assertTrue(flav["nutrition_unverified"])

    def test_audit_herkent_ontbrekende_receptmatch(self):
        offer={"name":"Diepvries blauwe bessen 750 g","norm":"diepvries blauwe bessen 750 g",
               "quantity":750,"unit":"g","price":3.0,"original_price":5.0,
               "promotion_type":"","is_loyalty":False,"url":"https://example.com"}
        offers={"ah":[offer],"jumbo":[],"lidl":[]}
        empty={"ah":[],"jumbo":[],"lidl":[]}
        report=audit_promotions(offers,empty)
        group=report["ah"]["groups"]["Fruit"]
        self.assertEqual(group["recognized_offers"],1)
        self.assertEqual(group["unlinked_offers"],1)
        matched={"ah":[{"ingredients":[{"sale":True,
           "action":{"name":"Diepvries blauwe bessen 750 g"}}]}],"jumbo":[],"lidl":[]}
        report=audit_promotions(offers,matched)
        self.assertEqual(report["ah"]["groups"]["Fruit"]["linked_offers"],1)

    def test_audit_meldt_onbekende_verpakking(self):
        offer={"name":"Diepvries spinazie aanbieding",
               "norm":"diepvries spinazie aanbieding","quantity":None,
               "unit":None,"price":1.0,"original_price":2.0,
               "promotion_type":"","is_loyalty":False,"url":""}
        report=audit_promotions({"ah":[offer],"jumbo":[],"lidl":[]},
                                {"ah":[],"jumbo":[],"lidl":[]})
        self.assertEqual(report["ah"]["unlinked"][0]["reason"],"Verpakkingsmaat onbekend")

    def test_echt_actiealternatief_naast_goedkopere_schapprijs(self):
        regular={"product":"Jumbo huismerk kwark","cash_price":3.0,"sale":False}
        offer={"name":"Campina Magere Milde Kwark Naturel 1 kg",
               "norm":"campina magere milde kwark naturel 1 kg",
               "quantity":1000,"unit":"g","price":2.49,
               "original_price":3.49,"multi_buy_quantity":None,
               "multi_buy_price":None,"promotion_type":"vaste actieprijs",
               "url":"https://www.jumbo.com/aanbiedingen/"}
        alternative=alternative_offers("kwark",1400,"g",[offer],regular)
        self.assertEqual(len(alternative),1)
        self.assertEqual(alternative[0]["cash_price"],4.98)
        self.assertTrue(alternative[0]["more_expensive_than_selected"])

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
