import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from brede_maaltijdvarianten import DISHES,expanded_variants,cooking_steps
from receptenradar_catalog import ING,validate_dish_ingredients
from receptkwaliteit import dish_quality_issues

class WorldCuisineIntegrationTests(unittest.TestCase):
 def test_every_world_cuisine_variant_is_fully_specified(self):
  recipes=expanded_variants()
  self.assertGreaterEqual(len(recipes),40)
  self.assertGreaterEqual(len({c for c,*_ in DISHES}),15)
  for cuisine,title,category,minutes,lines in DISHES:
   with self.subTest(title=title):
    self.assertFalse(validate_dish_ingredients(title,lines))
    self.assertFalse(dish_quality_issues(title,category,lines))
    self.assertTrue(all(key in ING and qty>0 and unit in ("g","ml","st")
                        for key,qty,unit in lines))
    self.assertTrue(cooking_steps(title,lines))
 def test_protein_and_vegetables_in_all_meals(self):
  protein={"kipfilet","kipdij","tofu","tempeh","garnalen","zalm",
           "tonijn","varkenshaas","bruine_bonen","kikkererwten","linzen",
           "kidneybonen","bonen","mozzarella"}
  vegetable={"sperziebonen","paprika","spinazie","broccoli","wok",
             "paksoi","aubergine","wortel","courgette","bloemkool",
             "champignons","tomaten","spruiten","komkommer"}
  for _,title,_,_,lines in DISHES:
   keys={key for key,_,_ in lines}
   self.assertTrue(keys&protein,title)
   self.assertTrue(keys&vegetable,title)
if __name__=="__main__":unittest.main()
