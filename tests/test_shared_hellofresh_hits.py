import sys,unittest
sys.path.insert(0,'src')
from shared_hellofresh_hits import build
class SharedHits(unittest.TestCase):
 def test_shared_recipe_is_a_hit_without_fake_price(self):
  archive={'items':[{'title':'Stamppot met spinazie en boerenworst','source':'Mijn HelloFresh-kaarten','ingredients':[{'name':'spinazie'}],'category':'Vlees'}]}
  offer={'name':'Spinazie','norm':'spinazie','price':1,'original_price':2,'quantity':500,'unit':'g','valid_from':'2026-10-26','valid_until':'2026-11-01'}
  out=build({'ah':[offer]},[archive],today='2026-10-26')
  hit=out['stores']['ah'][0]
  self.assertTrue(hit['has_possible_offer']);self.assertIsNone(hit['checkout']);self.assertFalse(hit['complete'])
 def test_expired_and_future_promotions_not_claimed(self):
  archive={'items':[{'title':'Spinazie met kip','source':'Mijn HelloFresh-archief','local_page':3}]}
  offer={'name':'Spinazie','norm':'spinazie','price':1,'original_price':2,'quantity':500,'unit':'g','valid_from':'2026-11-02','valid_until':'2026-11-08'}
  hit=build({'ah':[offer]},[archive],today='2026-10-26')['stores']['ah'][0]
  self.assertFalse(hit['has_possible_offer']);self.assertEqual(hit['local_page'],3)
 def test_all_archives_included_without_source_ranking_limit(self):
  a={'items':[{'title':f'Spinazie gerecht {i}','source':'Mijn HelloFresh-archief'} for i in range(90)]}
  self.assertEqual(build({'ah':[]},[a])['shared_recipe_count'],90)

 def test_spinach_bread_juice_and_salad_are_not_ingredient_hits(self):
  archive={'items':[{'title':'Stamppot met spinazie','source':'Mijn HelloFresh-kaarten'}]}
  offers=[{'name':name,'norm':name.lower(),'price':1,'original_price':2,'quantity':500,'unit':'g','valid_from':'2026-10-26','valid_until':'2026-11-01'} for name in ['AH Borrelbrood feta spinazie','AH Groentesap komkommer spinazie','AH Saladbowl feta spinazie']]
  hit=build({'ah':offers},[archive],today='2026-10-26')['stores']['ah'][0]
  self.assertFalse(hit['has_possible_offer'])
