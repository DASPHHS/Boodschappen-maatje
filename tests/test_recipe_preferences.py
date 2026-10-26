import json,unittest
from pathlib import Path
class RecipePreferences(unittest.TestCase):
 def test_uploaded_card_quantities_are_not_invented(self):
  card=json.loads(Path('recepten/hello-fresh-kaarten.json').read_text())['items'][0]
  self.assertEqual(card['servings'],3)
  ingredients={x['name']:x for x in card['ingredients']}
  self.assertEqual(ingredients['aardappelen']['quantity'],600)
  self.assertEqual(ingredients['kastanjechampignons']['quantity'],320)
  self.assertEqual(ingredients['spinazie']['quantity'],200)
  self.assertEqual(ingredients['varkensboerenworst']['quantity'],3)
  self.assertIsNone(card['minutes'])
  self.assertEqual(card['price_status'],'Niet doorgerekend')
 def test_actual_price_scan_is_scheduled_half_hourly(self):
  self.assertIn("cron: '17,47 * * * *'",Path('.github/workflows/receptenradar.yml').read_text())
 def test_shopping_saving_profile_is_explicit(self):
  s=Path('recepten/index.html').read_text()
  self.assertIn('id="quick-savings"',s)
  self.assertIn('value="saving"',s)
  self.assertIn('vergeleken met de reguliere bronprijzen',s)
