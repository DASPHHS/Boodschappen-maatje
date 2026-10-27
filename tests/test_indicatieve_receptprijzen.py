import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from receptvarianten_schatting import estimate
from indicatieve_receptprijzen import build

class EstimatedTests(unittest.TestCase):
 def test_title_without_enough_evidence_is_excluded(self):
  self.assertIsNone(estimate({"title":"B.B. met R."}))
  self.assertIsNone(estimate({"title":"Heerlijke kip"}))
 def test_explicit_ingredients_only(self):
  r=estimate({"title":"Kipfilet met broccoli en rijst","source":"Test","cuisine":"Aziatisch"})
  self.assertIsNotNone(r)
  self.assertEqual({x[0] for x in r["ingredients"]},{"kipfilet","broccoli","rijst"})
  self.assertEqual(sum(x[1] for x in r["ingredients"] if x[0]=="broccoli"),1200)
 def test_incomplete_snapshot_no_false_checkout(self):
  r=build({"ah":[]},{"ah":[]},items=[{"title":"Kipfilet met broccoli en rijst"}])
  self.assertEqual(r["ah"],[])
 def test_price_is_marked_as_partial(self):
  def p(name,qty,price):
   from receptenradar_v2 import normalize
   return {"name":name,"norm":normalize(name),"quantity":qty,"unit":"g",
     "price":price,"size_label":str(qty)+" g","url":"https://example.com"}
  r=build({"ah":[p("AH Kipfilet",700,7),p("AH Broccoli",600,2),p("AH Zilvervliesrijst",400,1.5)]},
          {"ah":[]},items=[{"title":"Kipfilet met broccoli en rijst"}])
  self.assertEqual(len(r["ah"]),1)
  self.assertTrue(r["ah"][0]["not_full_recipe"])
  self.assertEqual(r["ah"][0]["price_status"],"partial_estimate")
if __name__=="__main__":unittest.main()
