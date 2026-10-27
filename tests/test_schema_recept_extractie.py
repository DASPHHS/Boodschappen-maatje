import sys,unittest,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from schema_recept_extractie import extract

class SchemaRecipeTests(unittest.TestCase):
 def test_complete_recipe(self):
  data={"@context":"https://schema.org","@type":"Recipe",
    "name":"Kipfilet met broccoli en rijst","recipeYield":"4 personen",
    "totalTime":"PT30M","recipeCuisine":"Aziatisch",
    "recipeIngredient":["600 g kipfilet","800 g broccoli","300 g rijst"]}
  html='<script type="application/ld+json">'+json.dumps(data)+'</script>'
  recipe,reason=extract(html,"https://example.org/recept")
  self.assertIsNone(reason)
  self.assertEqual(recipe["servings"],4)
  self.assertEqual(len(recipe["ingredients"]),3)
 def test_missing_ingredient_not_silently_dropped(self):
  data={"@type":"Recipe","name":"Test","recipeYield":"4","totalTime":"PT30M",
    "recipeIngredient":["600 g kipfilet","800 g broccoli","een zakje onbekende saus"]}
  recipe,reason=extract('<script type="application/ld+json">'+json.dumps(data)+'</script>',"https://example.org/r")
  self.assertIsNone(recipe)
  self.assertEqual(reason,"incomplete_quantities_or_unknown_ingredient")
if __name__=="__main__":unittest.main()
