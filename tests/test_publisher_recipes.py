import unittest
from scripts import refresh_publisher_recipes as p
class TestPublisherMetadata(unittest.TestCase):
    def test_official_sitemap_parsing_and_targeting(self):
        xml='''<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>https://www.ah.nl/allerhande/recept/R-R123456/kikkererwtencurry-met-broccoli</loc></url>
        <url><loc>https://www.ah.nl/allerhande/recepten/curry</loc></url>
        <url><loc>https://evil.com/allerhande/recept/R-R1234/broccoli</loc></url></urlset>'''
        urls=p.candidates(xml,{},__import__('datetime').date(2026,11,1))
        self.assertEqual(len(urls),1)
        self.assertIn('R-R123456',urls[0][0])
    def test_structured_data_only_no_republish(self):
        import json
        meta={'@type':'Recipe','name':'Kip met groenten en zilvervliesrijst',
              'recipeCategory':'Hoofdgerecht','recipeYield':'4 personen',
              'totalTime':'PT35M','recipeIngredient':['400 gram kipfilet',
              '300 gram broccoli','2 wortelen','100 gram rijst','2 eetlepels olie',
              '100 gram tomaten'],'recipeInstructions':['Beschermde uitgeverstekst']}
        html='<script type="application/ld+json">'+json.dumps(meta)+'</script>'
        parsed=p.schema_recipes(html)
        self.assertEqual(len(parsed),1)
        r=p.to_record('https://www.ah.nl/allerhande/recept/R-R123456/kip-met-groenten',
                      parsed[0],'2026-11-01')
        self.assertEqual(r['servings'],4)
        self.assertEqual(r['minutes'],35)
        self.assertIn('broccoli',r['families'])
        self.assertIn('kip',r['families'])
        self.assertGreaterEqual(r['vegetable_families'],2)
        self.assertNotIn('recipeInstructions',r)
        self.assertNotIn('recipeIngredient',r)
    def test_reject_baby_dessert_and_no_vegetables(self):
        standard={'name':'Kip uit de pan met veel smaak','recipeYield':'4',
          'totalTime':'PT30M','recipeCategory':'hoofdgerecht',
          'recipeIngredient':['kipfilet 400 g','olie','ui','knoflook','kruiden']}
        url='https://www.ah.nl/allerhande/recept/R-R1234/kip-uit-de-pan'
        self.assertIsNone(p.to_record(url,standard,'2026-11-01'))
        standard['name']='Baby kip met paprika'
        standard['recipeIngredient'].append('400 g paprika')
        self.assertIsNone(p.to_record(url,standard,'2026-11-01'))
    def test_duration(self):
        self.assertEqual(p.minutes('PT1H25M'),85)
        self.assertEqual(p.minutes('PT30M'),30)
        self.assertIsNone(p.minutes('unknown'))

if __name__=="__main__":unittest.main()
