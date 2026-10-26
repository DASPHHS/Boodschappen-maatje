import sys,unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from bronrecept_controle import parse_recipe_page,verify_source_urls,matched_ingredient_keys,parse_yield

NOW=datetime(2026,10,26,13,0,tzinfo=timezone.utc)
SCHEMA="""<html><head><script type="application/ld+json">
{"@context":"https://schema.org","@type":"Recipe",
 "name":"Volkoren tonijnpasta met olijven",
 "recipeIngredient":["300 g volkoren penne","320 g tonijnstukken in water",
 "100 g zwarte olijven zonder pit","35 g kappertjes","2 courgettes"],
 "recipeYield":"4 personen",
 "aggregateRating":{"ratingValue":"4.6","ratingCount":"120"}}
</script></head></html>"""

class RecipeSourceTests(unittest.TestCase):
    def test_schema_ingr_portions(self):
        data=parse_recipe_page(SCHEMA)
        self.assertIsNotNone(data)
        self.assertEqual(data["ingredient_count"],5)
        self.assertEqual(data["servings"],4)
        self.assertEqual(data["rating"],4.6)
        self.assertEqual(data["level"],"bronrecept_4_personen")
        self.assertIn("pasta",data["recognized_ingredients"])
        self.assertIn("olijven",data["recognized_ingredients"])
        self.assertIn("kappertjes",data["recognized_ingredients"])

    def test_no_fake_verification_from_title_only(self):
        self.assertIsNone(parse_recipe_page("<h1>Pasta met tonijn</h1>"))
        self.assertIsNone(parse_yield("onbekend"))

    @patch("bronrecept_controle.robots_allowed",return_value=False)
    def test_dont_bypass_robots(self,allowed):
        class NoRequest:
            def get(self,*args,**kwargs):raise AssertionError("Netwerk bij robotsblokkade")
        cache,checks=verify_source_urls([
           {"title":"Tonijnpasta","url":"https://www.example.org/recipe","source":"Test"}
        ],{},NOW,limit=1,session=NoRequest())
        self.assertEqual(len(checks),1)
        self.assertEqual(checks[0]["level"],"niet_gecontroleerd")
        self.assertEqual(checks[0]["reason"],"robots_ontoegankelijk")

    @patch("bronrecept_controle.robots_allowed",return_value=True)
    def test_structured_source_not_priced(self,allowed):
        class Response:
            text=SCHEMA
            def raise_for_status(self):pass
        class Session:
            def get(self,*a,**kw):return Response()
        candidates=[{"title":"Volkoren tonijnpasta","url":"https://www.example.org/r","source":"Test"}]
        cache,checks=verify_source_urls(candidates,{},NOW,limit=1,session=Session())
        self.assertEqual(checks[0]["level"],"bronrecept_4_personen")
        self.assertEqual(cache[candidates[0]["url"]]["servings"],4)
        self.assertNotIn("price",cache[candidates[0]["url"]])
        again,checked=verify_source_urls(candidates,cache,NOW,limit=1,session=Session())
        self.assertEqual(checked,[],"Zelfde bron niet opnieuw ophalen binnen 3 dagen")

if __name__=="__main__":unittest.main()
