import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import refresh_hellofresh_recipes as hf
import refresh_publisher_recipes as ah

class IngredientEvidenceTests(unittest.TestCase):
    def test_hf_ingredient_evidence_comes_only_from_schema(self):
        url='https://www.hellofresh.nl/recipes/kip-met-broccoli-'+'a'*24
        page='<h1>Kip met broccoli en bloemkool</h1>'
        title=hf.record_from_page(url,page,'2026-11-02')
        self.assertEqual(title['ingredient_families'],[])
        self.assertEqual(title['ingredient_evidence'],'unavailable')
        page+='<script type="application/ld+json">'+json.dumps({'@type':'Recipe','recipeIngredient':['200 g kipfilet','1 broccoli']})+'</script>'
        record=hf.record_from_page(url,page,'2026-11-02')
        self.assertEqual(record['ingredient_families'],['broccoli','kip'])
        self.assertEqual(record['ingredient_evidence'],'publisher_recipe_schema')
        self.assertNotIn('instructions',record)
    def test_schema_can_identify_ingredients_absent_from_title(self):
        page='<h1>Indonesische zoete curry</h1><script type="application/ld+json">'+json.dumps({'@type':'Recipe','recipeIngredient':['200 g kippendijreepjes','1 wortel']})+'</script>'
        record=hf.record_from_page('https://www.hellofresh.nl/recipes/curry-'+'a'*24,page,'2026-11-02')
        self.assertEqual(record['ingredient_families'],['kip','wortel'])
    def test_sitemap_never_creates_ingredient_evidence(self):
        record=ah.sitemap_record('https://www.ah.nl/allerhande/recept/R-R123/kipcurry-met-broccoli','2026-11-02')
        self.assertNotIn('ingredient_families',record)
        self.assertNotIn('ingredient_evidence',record)
    def test_ah_ingredient_metadata(self):
        record=ah.to_record('https://www.ah.nl/allerhande/recept/R-R123/kipcurry',{
            'name':'Kipcurry met broccoli','recipeIngredient':['kipfilet','broccoli','zout','peper','olie'],
            'recipeCategory':'hoofdgerecht'},'2026-11-02')
        self.assertEqual(record['ingredient_families'],['broccoli','kip'])
        self.assertEqual(record['ingredient_evidence'],'publisher_recipe_schema')
