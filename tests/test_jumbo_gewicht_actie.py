import sys,unittest
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from receptenradar_v2 import measure_offer,offer_price,normalize

class WeightedOfferRegression(unittest.TestCase):
 def test_one_piece_405_grams(self):
  self.assertEqual(measure_offer({"name":"Jumbo Varkenshaas Culinair 1 Stuk ca. 405 g",
                                   "quantity":"1 stuk"}),(405.0,"g"))
 def test_known_sale_price_without_original_is_not_fake_discount(self):
  today=datetime.now(ZoneInfo("Europe/Amsterdam")).date().isoformat()
  o={"name":"Jumbo Varkenshaas Culinair 1 Stuk ca. 405 g",
     "norm":normalize("Jumbo Varkenshaas Culinair 1 Stuk ca. 405 g"),
     "price":4.82,"original_price":None,
     "quantity":405,"unit":"g","size_label":"405 g",
     "valid_from":today,"valid_until":today,
     "promotion_type":"", "multi_buy_quantity":None,"multi_buy_price":None,
     "is_loyalty":False,"url":"https://www.jumbo.com/"}
  rows=offer_price("varkenshaas",800,"g",[o])
  self.assertEqual(len(rows),1)
  self.assertEqual(rows[0]["cash_price"],9.64)
  self.assertEqual(rows[0]["packages"],2)
  self.assertFalse(rows[0]["sale"])
if __name__=="__main__":unittest.main()
