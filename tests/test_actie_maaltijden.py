"""Test dat de maaltijdgenerator aanbiedingen als input gebruikt."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from actie_maaltijden import classify_offers,meal_candidates

def sale(name,unit="g",amount=600,discount=30):
 return {"name":name,"norm":name.lower(),"unit":unit,"quantity":amount,
         "discount":discount,"price":2,"original_price":3,
         "valid_until":"2026-10-27","promotion_type":"actie",
         "multi_buy_quantity":None,"multi_buy_price":None,"is_loyalty":False}

class OfferDrivenTest(unittest.TestCase):
 def test_drie_aanbiedingen_geven_complete_maaltijd(self):
  products=[sale("varkenshaas",amount=400),sale("broccoli",amount=800),
            sale("krieltjes",amount=600)]
  candidates=meal_candidates(products)
  self.assertTrue(candidates)
  self.assertTrue(any({key for key,_,_ in recipe[3]}=={"varkenshaas","broccoli","aardappel"}
       for recipe in candidates))
 def test_geen_maaltijden_zonder_eiwit_of_groente(self):
  self.assertEqual(meal_candidates([sale("broccoli"),sale("krieltjes")]),[])
  self.assertEqual(meal_candidates([sale("kipfilet"),sale("krieltjes")]),[])
 def test_geen_dranken_of_pseudovlees(self):
  items=[sale("vegetarische kipfilet"),sale("gewassen spinazie")]
  self.assertFalse(meal_candidates(items))
 def test_vier_actieingredienten_mogelijk(self):
  items=[sale("kipfilet"),sale("broccoli"),sale("paprika",unit="st",amount=2),sale("krieltjes")]
  recipes=meal_candidates(items)
  self.assertTrue(any(len(r[3])==4 for r in recipes))
 def test_geen_kipgehakt_spinazie_boerenkool(self):
  items=[sale("kipgehakt"),sale("spinazie"),sale("boerenkool"),sale("krieltjes"),sale("paprika",unit="st",amount=2)]
  recipes=meal_candidates(items)
  self.assertFalse(any({"kipgehakt","spinazie","boerenkool"}.issubset(
      {key for key,_,_ in recipe[3]}) for recipe in recipes))
 def test_herkenbare_maaltijd(self):
  items=[sale("kipgehakt"),sale("spinazie"),sale("champignons"),sale("volkoren pasta")]
  recipes=meal_candidates(items)
  self.assertTrue(any({"kipgehakt","spinazie","champignons","pasta"}.issubset(
      {key for key,_,_ in recipe[3]}) for recipe in recipes))
 def test_royale_hoeveelheid_eiwitcomponent(self):
  items=[sale("kipfilet"),sale("broccoli")]
  meals=meal_candidates(items)
  self.assertTrue(any(
      ("kipfilet",800,"g") in recipe[3] for recipe in meals))
 def test_variatie(self):
  items=[sale("kipfilet"),sale("varkenshaas"),sale("broccoli"),sale("spruitjes"),sale("krieltjes")]
  cs=meal_candidates(items)
  self.assertGreaterEqual(len(cs),4)
  self.assertTrue(all(x[1] in ("Kip","Vlees") for x in cs))
if __name__=="__main__":unittest.main()
