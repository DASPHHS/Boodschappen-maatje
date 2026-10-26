import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from receptenradar_v2 import match_ingredient, ingredient_price, offer_price, make_recipes
from product_compatibiliteit import compatible,recipe_line_errors

def p(name,price=1.0,qty=400,unit="g"):
    from receptenradar_v2 import normalize
    return {"name":name,"norm":normalize(name),"price":price,"quantity":qty,
            "unit":unit,"size_label":str(qty)+" "+unit,"url":"https://example.org/p"}
def o(name,price=1.0,original=3,qty=400,unit="g"):
    x=p(name,price,qty,unit)
    x.update({"original_price":original,"multi_buy_quantity":None,
              "multi_buy_price":None,"promotion_type":"30% korting",
              "valid_until":"2026-10-27","is_loyalty":False})
    return x

class SemanticProductTest(unittest.TestCase):
    def test_reject_false_fruit(self):
        for name in ["Hero Fruitspread blauwe bessen","Ella's kitchen Baby bosbessen ontbijtje 6m+",
                     "AH Blauwe bessen yoghurt","AH Bosbessen siroop"]:
            self.assertFalse(match_ingredient(p(name),"blauwe_bessen"),name)
        for name in ["AH Terra Plantaardige soja gurt aardbei",
                     "Olvarit Appel aardbei peer 6m+","Aardbeien jam"]:
            self.assertFalse(match_ingredient(p(name),"aardbeien"),name)
        for name in ["AH Blauwe bessen","AH Diepvries blauwe bessen",
                     "Jumbo Bosbessen"]:
            self.assertTrue(match_ingredient(p(name),"blauwe_bessen"),name)
        self.assertTrue(match_ingredient(p("AH Aardbeien"),"aardbeien"))
    def test_no_spurious_actions(self):
        offer_list=[o("Olvarit Appel aardbei peer 6m+",.99,2.2),
                    o("AH Aardbeien",2.99,3.99)]
        results=offer_price("aardbeien",450,"g",offer_list)
        self.assertEqual([r["product"] for r in results],["AH Aardbeien"])
        self.assertFalse(offer_price("blauwe_bessen",350,"g",
                                    [o("Ella's kitchen Baby bosbessen ontbijtje 6m+",.4,2)]))
    def test_compatibility_prepared_and_fresh(self):
        pairs=[
            ("AH Amsterdamse uien","ui"),("Bonduelle Doperwtjes & worteltjes","wortel"),
            ("Knorr Trattoria kipfilet romana","kipfilet"),
            ("Olvarit Rode bietstamppot met kikkererwten 6m+","kikkererwten"),
            ("Olvarit Spinazie kip aardappel 12m+","spinazie"),
            ("AH Half-om-half gehakt","gehakt"),
            ("Alpro Plantaardige kwark naturel","kwark"),
            ("AH Tomatensoep","tomaten"),("Hero Fruitspread blauwe bessen","blauwe_bessen")
        ]
        for name,ing in pairs:
            self.assertFalse(compatible(name,ing),name)
        for name,ing in [
            ("AH Rundergehakt","gehakt"),("AH Diepvries spinazie","spinazie"),
            ("AH Bospeen","wortel"),("AH Uien","ui"),
            ("AH Kik­kererwten","kikkererwten"),("AH Volkoren pasta","pasta"),
            ("De Zaanse Hoeve Magere kwark","kwark")
        ]:
            self.assertTrue(compatible(name,ing),name)
    def test_warung_prepared_meal_not_shoarma_ingredient(self):
        product="Warung Turkse rijst kipshoarma"
        self.assertFalse(compatible(product,"shoarma"))
        self.assertFalse(match_ingredient(p(product,4.99,450),"shoarma"))
        self.assertEqual(offer_price("shoarma",600,"g",[o(product,4.99,6.39,450)]),[])
        chosen=ingredient_price("shoarma",600,"g",
             [p(product,6.39,450),p("AH Scharrel kip shoarma",5.79,400)],
             [o(product,4.99,6.39,450)])
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen["product"],"AH Scharrel kip shoarma")
        self.assertFalse(chosen["sale"])
    def test_generic_composite_meals_are_not_raw_ingredients(self):
        cases=[
            ("Kip met rijst en groenten","kipfilet"),
            ("Zalm met rijst","zalm"),
            ("Nasi goreng met kip","rijst"),
            ("Bami met kip","kipdij"),
            ("Pasta met tonijn","tonijn"),
            ("Verse rijstmaaltijd met groenten","rijst"),
            ("Bereide rijst met kip","rijst"),
            ("Complete maaltijd met kikkererwten","kikkererwten"),
            ("Ovengerecht ovenschotel broccoli","broccoli")
        ]
        for name,key in cases:
            self.assertFalse(compatible(name,key),(name,key))
        for name,key in [
            ("AH Verse kipfilet","kipfilet"),
            ("AH Rauwe zalmfilet","zalm"),
            ("AH Basmati rijst","rijst"),
            ("AH Verse broccoli","broccoli"),
            ("AH Kipshoarma gekruid","shoarma")
        ]:
            self.assertTrue(compatible(name,key),(name,key))
    def test_cheapest_real_berries_not_spread(self):
        shelves=[
            p("Hero Fruitspread blauwe bessen",1.99,350),
            p("AH Blauwe bessen",3.79,250),
            p("AH Diepvries blauwe bessen",2.49,300),
        ]
        r=ingredient_price("blauwe_bessen",400,"g",shelves,[])
        self.assertTrue(r)
        self.assertIn("bessen",r["product"])
        self.assertNotIn("Fruitspread",r["product"])
        self.assertEqual(r["cash_price"],4.98)
    def test_no_invalid_recipe_lines(self):
        self.assertTrue(recipe_line_errors({"ingredients":[{"key":"blauwe_bessen","product":"Hero Fruitspread blauwe bessen"}]}))
        self.assertEqual(recipe_line_errors({"ingredients":[{"key":"blauwe_bessen","product":"AH Blauwe bessen"}]}),[])

if __name__=="__main__":unittest.main()
