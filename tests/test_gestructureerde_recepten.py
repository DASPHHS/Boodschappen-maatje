import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from gestructureerde_recepten import convert,load

class StructuredRecipesTests(unittest.TestCase):
 def test_reject_title_only(self):
  r,reason=convert({"title":"B.B. met R. (bruine bonen met rijst)"})
  self.assertIsNone(r)
  self.assertEqual(reason,"no_complete_ingredient_list")
 def test_four_person_conversion(self):
  r,reason=convert({"title":"Kip met groenten","servings":2,"category":"Kip","minutes":30,
      "ingredients":[{"name":"kipfilet","quantity":300,"unit":"g"},
       {"name":"broccoli","quantity":250,"unit":"g"},
       {"name":"rijst","quantity":160,"unit":"g"}]})
  self.assertIsNone(reason)
  self.assertEqual(r["ingredients"],[("kipfilet",600,"g"),("broccoli",500,"g"),("rijst",320,"g")])
 def test_reject_unknown_core_component(self):
  r,reason=convert({"title":"Stamppot met boerenworst","servings":3,
      "ingredients":[{"name":"aardappelen","quantity":600,"unit":"g"},
       {"name":"boerenworst","quantity":3,"unit":"st"},
       {"name":"spinazie","quantity":200,"unit":"g"}]})
  self.assertIsNone(r)
  self.assertEqual(reason,"unmapped_ingredient")
 def test_repo_archive_has_rejections(self):
  accepted,rejections=load()
  self.assertGreater(rejections.get("no_complete_ingredient_list",0),50)
if __name__=="__main__":unittest.main()
