"""Test dat de maaltijdgenerator aanbiedingen als input gebruikt."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from actie_maaltijden import classify_offers,meal_candidates,DISH_TEMPLATES

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
 def test_alle_automatische_recepten_zijn_echte_templates(self):
  items=[sale("kipfilet"),sale("kipshoarma"),sale("broccoli"),
         sale("wokgroenten"),sale("krieltjes"),sale("volkoren pasta")]
  dishes=meal_candidates(items)
  known={x[4] for x in DISH_TEMPLATES}
  self.assertTrue(dishes)
  self.assertTrue(all(d[0] in known for d in dishes))
  self.assertFalse(any(d[0]=="Kipfilet met wokgroenten en volkoren pasta" for d in dishes))
  self.assertTrue(any("Kipshoarma met" in d[0] for d in dishes))
 def test_geen_pasta_zonder_uitgewerkt_gerecht(self):
  items=[sale("kipfilet"),sale("wokgroenten"),sale("volkoren pasta")]
  self.assertFalse(any({x[0] for x in d[3]}=={"kipfilet","wok","pasta"}
      for d in meal_candidates(items)))
 def test_onbewezen_actie_kan_geen_recept_aanjagen(self):
  kip=sale("kipfilet")
  broccoli=sale("broccoli")
  kip["price"]=3
  kip["original_price"]=3
  self.assertEqual(meal_candidates([kip,broccoli]),[])
  # Geldige 2-voor-actie blijft bruikbaar, ook bij gelijke losse prijs.
  kip["multi_buy_quantity"]=2
  kip["multi_buy_price"]=5
  self.assertTrue(meal_candidates([kip,broccoli]))

 def test_naan_aanbiedingen_koppelen_aan_passende_eiwitten_en_groenten(self):
  products=[sale("kipfilet"),sale("broccoli"),sale("naanbrood 2 st",unit="st",amount=2)]
  recipes=meal_candidates(products)
  self.assertTrue(any(
   {"kipfilet","broccoli","naan"} == {i[0] for i in x[3]} for x in recipes
  ))
 def test_maaltijdpakket_is_nooit_kip_of_andere_eiwitbron(self):
  products=[sale("Knorr Wereldgerechten Kip Tandoori maaltijdpakket"),
            sale("broccoli"),sale("naanbrood 2 st",unit="st",amount=2)]
  self.assertFalse(meal_candidates(products))
 def test_garnalen_als_zelfstandige_eiwitbron(self):
  products=[sale("garnalen"),sale("wokgroenten"),sale("naanbrood 2 st",unit="st",amount=2)]
  self.assertTrue(any(x[1]=="Vis" and "garnalen" in {i[0] for i in x[3]}
                      for x in meal_candidates(products)))

 def test_variatie(self):
  items=[sale("kipfilet"),sale("varkenshaas"),sale("broccoli"),sale("spruitjes"),sale("krieltjes")]
  cs=meal_candidates(items)
  self.assertGreaterEqual(len(cs),4)
  self.assertTrue(all(x[1] in ("Kip","Vlees") for x in cs))
if __name__=="__main__":unittest.main()
